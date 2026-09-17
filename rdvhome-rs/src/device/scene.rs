// A scene: switching it on switches the other scenes off, optionally switches
// some lights on, then paints every coloured light that is on. With a timeout
// it keeps repainting until it is switched off, without one it paints once and
// goes off by itself (it behaves like a push button).

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, OnceLock, Weak};
use std::time::Duration;

use async_trait::async_trait;
use rand::Rng;

use super::{Capabilities, Command, Device, Effect, Report};
use crate::color::Hsb;
use crate::switch::{Home, Switch};

pub enum Colors {
    // a new random colour every time
    Random,
    Fixed(Hsb),
    // every light starts from its place in the list and walks it
    Cycle(Vec<Hsb>),
    // a random walk: every colour is the one before moved a bit. None starts from a random colour.
    Perturb { base: Option<Hsb>, factor: f64 },
}

pub enum Effects {
    // no nanoleaf effect: an animation around the colour of the scene
    None,
    Same(String),
    // every panel has different effects installed: (switch id, effect)
    PerSwitch(Vec<(String, String)>),
}

pub struct Scene {
    pub id: String,
    pub colors: Colors,
    pub effects: Effects,
    // seconds between repaints, (min, max)
    pub timeout: Option<(f64, f64)>,
    // aliases to switch on with the scene
    pub turn_on: Vec<String>,
    on: AtomicBool,
    // every switch on/off is a new generation: old repaint loops see it and stop
    generation: AtomicU64,
    home: OnceLock<Weak<Home>>,
}

fn perturb(color: Hsb, factor: f64) -> Hsb {
    let mut rng = rand::rng();
    let mut delta = || (rng.random::<f64>() * 2.0 - 1.0) * factor;

    Hsb {
        saturation: Some((color.saturation.unwrap_or(0.0) + delta()).clamp(0.5, 1.0)),
        hue: Some((color.hue.unwrap_or(0.0) + delta()).rem_euclid(1.0)),
        brightness: None,
    }
}

impl Scene {
    pub fn new(id: &str, colors: Colors, effects: Effects, timeout: Option<(f64, f64)>, turn_on: &[&str]) -> Arc<Scene> {
        Arc::new(Scene {
            id: id.to_string(),
            colors,
            effects,
            timeout,
            turn_on: turn_on.iter().map(|a| a.to_string()).collect(),
            on: AtomicBool::new(false),
            generation: AtomicU64::new(0),
            home: OnceLock::new(),
        })
    }

    // scenes act on the other switches
    pub fn attach(&self, home: &Arc<Home>) {
        let _ = self.home.set(Arc::downgrade(home));
    }

    fn report(&self) -> Report {
        Report { on: Some(self.on.load(Ordering::SeqCst)), ..Report::full() }
    }

    fn active(&self, generation: u64) -> bool {
        self.on.load(Ordering::SeqCst) && self.generation.load(Ordering::SeqCst) == generation
    }

    // the n-th command for the light at place i
    fn command(&self, switch: &Switch, i: usize, n: usize, previous: Option<Hsb>) -> Command {
        let color = match &self.colors {
            Colors::Random => Hsb::random(),
            Colors::Fixed(color) => *color,
            Colors::Cycle(colors) => colors[(i + n) % colors.len()],
            Colors::Perturb { base, factor } => match previous.or(*base) {
                Some(color) => perturb(color, *factor),
                None => Hsb::random(),
            },
        };

        let effect = match &self.effects {
            Effects::None => None,
            Effects::Same(name) => Some(name.clone()),
            Effects::PerSwitch(names) => names.iter().find(|(id, _)| *id == switch.id).map(|(_, name)| name.clone()),
        };

        Command {
            color: Some(color),
            effect: Some(match effect {
                Some(name) => Effect::Named(name),
                None if matches!(self.colors, Colors::Random) => Effect::Highlight(Hsb::random()),
                None => Effect::Highlight(color),
            }),
            ..Command::default()
        }
    }

    async fn paint(self: Arc<Self>, switch: Arc<Switch>, i: usize, generation: u64) {
        let mut previous = None;

        for n in 0.. {
            if switch.device.is_on().await {
                let cmd = self.command(&switch, i, n, previous);
                previous = cmd.color;
                switch.apply(&cmd).await;
            }

            let Some((min, max)) = self.timeout else { return };
            let seconds = rand::rng().random::<f64>() * (max - min) + min;
            tokio::time::sleep(Duration::from_secs_f64(seconds)).await;

            if !self.active(generation) {
                return;
            }
        }
    }
}

// Scene needs itself as an Arc for the repaint tasks: the device is the Arc.
pub struct SceneDevice(pub Arc<Scene>);

#[async_trait]
impl Device for SceneDevice {
    fn capabilities(&self) -> Capabilities {
        Capabilities::ON
    }

    async fn read(&self) -> Report {
        self.0.report()
    }

    async fn apply(&self, cmd: &Command) -> Report {
        let scene = &self.0;
        let (Some(on), Some(home)) = (cmd.on, scene.home.get().and_then(Weak::upgrade)) else { return scene.report() };

        if on == scene.on.swap(on, Ordering::SeqCst) {
            return scene.report();
        }

        let generation = scene.generation.fetch_add(1, Ordering::SeqCst) + 1;

        if on {
            let lights = home.filter_any(&scene.turn_on);
            let scenes: Vec<_> = home.filter(Some("control")).into_iter().filter(|s| s.id != scene.id).collect();

            let (turn_on, turn_off) = (Command::on(true), Command::on(false));
            tokio::join!(Home::apply(&lights, &turn_on), Home::apply(&scenes, &turn_off));

            for (i, switch) in home.filter(Some("switch")).into_iter().enumerate() {
                if switch.device.capabilities().hue {
                    tokio::spawn(scene.clone().paint(switch, i, generation));
                }
            }

            if scene.timeout.is_none() {
                let (scene, home) = (scene.clone(), home.clone());

                tokio::spawn(async move {
                    tokio::time::sleep(Duration::from_millis(500)).await;

                    if scene.active(generation) {
                        Home::apply(&home.filter(Some(&scene.id)), &Command::on(false)).await;
                    }
                });
            }
        }

        scene.report()
    }

    async fn is_on(&self) -> bool {
        self.0.on.load(Ordering::SeqCst)
    }
}
