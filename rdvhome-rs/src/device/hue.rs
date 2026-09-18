// Philips Hue. HueBridge owns the http api and the poll loop, HueLight is one
// zigbee bulb. The bridge is asked every 3 seconds and feeds its lights, so a
// light answers read() from what it last saw (saved in remote-<key>.json, which
// also survives a restart), never from the network.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Number, Value};
use tokio::sync::broadcast;

use super::{changes, Capabilities, Changes, ColorReport, Command, Device, Report};
use crate::color::{Hsb, PHILIPS};
use crate::store::Store;

const POLL: Duration = Duration::from_secs(3);

// what a bulb shows when the mains comes back: not a colour anyone chose
const POWER_ON_COLOR: Hsb =
    Hsb { hue: Some(0.12845044632639047), saturation: Some(0.5511811023622047), brightness: Some(1.0) };

#[derive(Clone)]
struct Api {
    client: reqwest::Client,
    // http://<host>/api/<token>/lights/
    base: String,
}

pub struct HueBridge {
    api: Api,
    store: Store,
    lights: Mutex<Vec<Arc<HueLight>>>,
    started: AtomicBool,
}

#[derive(Clone, Copy)]
pub struct HueOptions {
    // false for a plain white bulb or a plug
    pub color: bool,
    // the mains goes through a relay: unreachable means "no power", not "off"
    pub behind_relay: bool,
}

impl Default for HueOptions {
    fn default() -> Self {
        HueOptions { color: true, behind_relay: false }
    }
}

impl HueBridge {
    pub fn new(host: &str, token: &str, store: Store) -> Arc<HueBridge> {
        Arc::new(HueBridge {
            api: Api { client: crate::device::http_client(), base: format!("http://{}/api/{}/lights/", host, token) },
            store,
            lights: Mutex::default(),
            started: AtomicBool::new(false),
        })
    }

    // `key` names the saved state file, the old app used the switch id
    pub fn light(&self, id: u32, key: &str, options: HueOptions) -> Arc<HueLight> {
        let light = Arc::new(HueLight {
            api: self.api.clone(),
            store: self.store.clone(),
            id,
            key: key.to_string(),
            options,
            changes: changes(),
            commanded: Mutex::new(Instant::now()),
        });

        self.lights.lock().unwrap().push(light.clone());
        light
    }

    async fn poll(&self) -> Result<(), reqwest::Error> {
        let asked = Instant::now();
        let payload: Map<String, Value> = self.api.client.get(&self.api.base).send().await?.json().await?;
        let lights = self.lights.lock().unwrap().clone();

        for light in lights {
            if let Some(state) = payload.get(&light.id.to_string()).and_then(|l| l.get("state")) {
                // an answer older than the last command would undo it
                if *light.commanded.lock().unwrap() < asked {
                    light.sync(state).await;
                }
            }
        }

        Ok(())
    }
}

// The bridge is listed between the switches (invisible, as "philips_pool"): it
// has nothing to switch, its job is the poll loop.
#[async_trait]
impl Device for HueBridge {
    fn capabilities(&self) -> Capabilities {
        Capabilities { visibility: false, ..Capabilities::NONE }
    }

    async fn read(&self) -> Report {
        Report::full()
    }

    async fn apply(&self, _cmd: &Command) -> Report {
        Report::full()
    }

    fn start(self: Arc<Self>) {
        if self.started.swap(true, Ordering::SeqCst) {
            return;
        }

        tokio::spawn(async move {
            loop {
                if let Err(e) = self.poll().await {
                    eprintln!("hue bridge: {}", e);
                }
                tokio::time::sleep(POLL).await;
            }
        });
    }
}

#[derive(Clone, Serialize, Deserialize)]
struct Saved {
    on: bool,
    allow_on: bool,
    hue: Number,
    brightness: Number,
    saturation: Number,
}

impl Default for Saved {
    fn default() -> Self {
        Saved { on: false, allow_on: true, hue: number(0.5), brightness: Number::from(1), saturation: Number::from(1) }
    }
}

impl Saved {
    fn color(&self) -> Hsb {
        Hsb { hue: self.hue.as_f64(), saturation: self.saturation.as_f64(), brightness: self.brightness.as_f64() }
    }

    fn set_color(&mut self, color: &Hsb) {
        for (target, value) in [
            (&mut self.hue, color.hue),
            (&mut self.saturation, color.saturation),
            (&mut self.brightness, color.brightness),
        ] {
            if let Some(value) = value {
                *target = number(value);
            }
        }
    }
}

// the old app writes a zero as the integer 0
pub fn number(value: f64) -> Number {
    match Number::from_f64(value) {
        Some(number) if value != 0.0 => number,
        _ => Number::from(0),
    }
}

pub struct HueLight {
    api: Api,
    store: Store,
    id: u32,
    key: String,
    options: HueOptions,
    changes: Changes,
    // when the last command was done
    commanded: Mutex<Instant>,
}

impl HueLight {
    fn saved(&self) -> Saved {
        self.store.get(&self.key).unwrap_or_default()
    }

    // The bridge tells what the bulb is doing now (the "state" of GET /lights/).
    async fn sync(&self, state: &Value) {
        let reachable = state["reachable"].as_bool().unwrap_or(false);
        let on = reachable && state["on"].as_bool().unwrap_or(false);
        let allow_on = reachable || self.options.behind_relay;

        let mut color = state.get("hue").map(|_| {
            let component = |key: &str, max: f64| state[key].as_f64().map(|v| v / max);
            Hsb {
                hue: component("hue", PHILIPS.hue),
                saturation: component("sat", PHILIPS.saturation),
                brightness: component("bri", PHILIPS.brightness),
            }
        });

        let mut saved = self.saved();
        let mut saved_color = saved.color();
        let mut changed = false;

        // the mains came back and the bulb forgot its colour: give it back
        if reachable && color.is_some_and(|c| c.same(&POWER_ON_COLOR)) {
            if saved_color.same(&POWER_ON_COLOR) {
                // even the saved colour is the power-on one: nothing of ours to restore
                saved_color = Saved::default().color();
            } else {
                saved_color.brightness = Some(1.0);
            }

            println!("[HUE {}] came up on the bridge power-on colour, pushing back {:?}", self.key, saved_color);

            self.apply(&Command { color: Some(saved_color), ..Command::default() }).await;
            color = Some(saved_color);
            changed = true;
        }

        if self.options.behind_relay {
            // without mains the zigbee state is unknown: keep the last one
            changed |= reachable && on != saved.on;
        } else {
            changed |= on != saved.on || allow_on != saved.allow_on;
        }

        changed |= color.is_some_and(|c| !c.same(&saved_color));

        if changed {
            if on != saved.on {
                println!("[HUE {}] bridge says on={} (was {}), reachable={}", self.key, on, saved.on, reachable);
            }

            saved.on = on;
            saved.allow_on = allow_on;
            if let Some(color) = color {
                saved.set_color(&color);
            }
            self.store.set(&self.key, &saved);

            let _ = self.changes.send(());
        }
    }
}

#[async_trait]
impl Device for HueLight {
    fn capabilities(&self) -> Capabilities {
        if self.options.color {
            Capabilities::COLOR
        } else {
            Capabilities::ON
        }
    }

    async fn read(&self) -> Report {
        let saved = self.saved();

        Report {
            on: Some(saved.on),
            allow_on: Some(saved.allow_on),
            color: Some(ColorReport::Stored { hue: saved.hue, brightness: saved.brightness, saturation: saved.saturation }),
            ..Report::full()
        }
    }

    async fn apply(&self, cmd: &Command) -> Report {
        let mut request = Map::new();

        if let Some(on) = cmd.on {
            request.insert("on".into(), json!(on));
        }

        if let Some(color) = &cmd.color {
            for (key, value) in ["hue", "sat", "bri"].into_iter().zip(color.scaled(PHILIPS)) {
                if let Some(value) = value {
                    request.insert(key.into(), json!(value));
                }
            }
        }

        if !request.is_empty() {
            let url = format!("{}{}/state", self.api.base, self.id);

            // the answer lists what was refused (a colour for a light that is off): nothing to do about it
            if let Err(e) = self.api.client.put(url).json(&request).send().await {
                eprintln!("hue light {}: {}", self.key, e);
            }
        }

        let mut saved = self.saved();
        if let Some(on) = cmd.on {
            saved.on = on;
        }
        if let Some(color) = &cmd.color {
            saved.set_color(color);
        }
        self.store.set(&self.key, &saved);
        *self.commanded.lock().unwrap() = Instant::now();

        Report::echo(cmd)
    }

    async fn is_on(&self) -> bool {
        self.saved().on
    }

    fn changes(&self) -> Option<broadcast::Receiver<()>> {
        Some(self.changes.subscribe())
    }
}
