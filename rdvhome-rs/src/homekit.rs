// The house as a HomeKit bridge: every switch becomes an accessory, in the
// same order and with the same ids the old app gave them (see hap/accessory.rs),
// so the Home app keeps its rooms, names and automations.
//
//   switch events  ->  characteristic values (and EVENTs to the iPhones)
//   writes of the iPhones  ->  commands to the switches

use std::path::PathBuf;
use std::sync::{Arc, OnceLock};

use serde_json::{json, Value};
use tokio::sync::broadcast::error::RecvError;

use crate::color::Hsb;
use crate::device::{ColorReport, Command, Direction, Report};
use crate::hap::accessory::{Accessory, Kind, BRIGHTNESS, HUE, ON, SATURATION};
use crate::hap::state::State;
use crate::hap::{Hap, CATEGORY_BRIDGE};
use crate::switch::{Home, Switch};

pub const PORT: u16 = 51826;

// how a switch shows up in the Home app
#[derive(Clone, Copy, PartialEq)]
pub enum Homekit {
    Hidden,
    Switch,
    Lightbulb,
    // two switches, "<name> Up" and "<name> Down"
    Window,
}

#[derive(Clone, Copy, PartialEq)]
enum Role {
    Main,
    Up,
    Down,
}

struct Binding {
    aid: u64,
    switch: Arc<Switch>,
    role: Role,
}

static RUNNING: OnceLock<Arc<Hap>> = OnceLock::new();

pub struct Pairing {
    pub paircode: String,
    pub uri: String,
}

impl Pairing {
    fn code(&self) -> Option<qrcode::QrCode> {
        qrcode::QrCode::new(self.uri.as_bytes()).ok()
    }

    pub fn qrcode_svg(&self) -> String {
        self.code().map_or_else(String::new, |code| code.render::<qrcode::render::svg::Color>().min_dimensions(462, 462).build())
    }

    pub fn qrcode_text(&self) -> String {
        self.code().map_or_else(String::new, |code| code.render::<qrcode::render::unicode::Dense1x2>().build())
    }
}

fn state_file(data: PathBuf) -> PathBuf {
    let _ = std::fs::create_dir_all(&data);
    data.join("accessory.state")
}

// of the running server, or (for `rdvhome pair`) of the state on disk
pub fn pairing(data: Option<PathBuf>) -> Option<Pairing> {
    match (RUNNING.get(), data) {
        (Some(hap), _) => Some(Pairing { paircode: hap.pincode(), uri: hap.setup_uri() }),
        (None, Some(data)) => {
            let state = State::load(state_file(data));
            Some(Pairing { paircode: state.pincode.clone(), uri: state.setup_uri(CATEGORY_BRIDGE) })
        }
        (None, None) => None,
    }
}

fn bindings(home: &Home) -> Vec<Binding> {
    // hap-python counted from 2 (1 is the bridge) and skipped 7
    let mut aids = (2..).filter(|aid| *aid != 7);
    let mut out = Vec::new();

    for switch in &home.switches {
        let roles: &[Role] = match switch.homekit {
            Homekit::Hidden => &[],
            Homekit::Window => &[Role::Up, Role::Down],
            _ => &[Role::Main],
        };

        for role in roles {
            out.push(Binding { aid: aids.next().unwrap(), switch: switch.clone(), role: *role });
        }
    }

    out
}

fn accessories(name: &str, bindings: &[Binding]) -> Vec<Accessory> {
    let mut out = vec![Accessory::new(1, name, Kind::Bridge)];

    for binding in bindings {
        let switch = &binding.switch;

        out.push(match (switch.homekit, binding.role) {
            (Homekit::Lightbulb, _) => Accessory::new(binding.aid, &switch.name, Kind::Lightbulb { color: switch.device.capabilities().hue }),
            (_, Role::Up) => Accessory::new(binding.aid, &format!("{} Up", switch.name), Kind::Switch),
            (_, Role::Down) => Accessory::new(binding.aid, &format!("{} Down", switch.name), Kind::Switch),
            _ => Accessory::new(binding.aid, &switch.name, Kind::Switch),
        });
    }

    out
}

fn publish(hap: &Hap, binding: &Binding, report: &Report) {
    match (binding.role, report.moving) {
        (Role::Up, Some((up, _))) => hap.set_value(binding.aid, ON, json!(up)),
        (Role::Down, Some((_, down))) => hap.set_value(binding.aid, ON, json!(down)),
        _ => {}
    }

    if binding.role != Role::Main {
        return;
    }

    if let Some(on) = report.on {
        hap.set_value(binding.aid, ON, json!(on));
    }

    let color = match &report.color {
        Some(ColorReport::Stored { hue, brightness, saturation }) => {
            Hsb { hue: hue.as_f64(), saturation: saturation.as_f64(), brightness: brightness.as_f64() }
        }
        Some(ColorReport::Applied(color)) => *color,
        None => return,
    };

    for (iid, value, max) in [(HUE, color.hue, 360.0), (SATURATION, color.saturation, 100.0), (BRIGHTNESS, color.brightness, 100.0)] {
        if let Some(value) = value {
            hap.set_value(binding.aid, iid, json!((value * max) as i64));
        }
    }
}

fn command(role: Role, iid: u64, value: &Value) -> Option<Command> {
    let number = value.as_f64();

    Some(match (role, iid) {
        (Role::Main, ON) => Command::on(value.as_bool()?),
        (Role::Main, HUE) => Command { color: Some(Hsb { hue: Some(number? / 360.0), ..Hsb::default() }), ..Command::default() },
        (Role::Main, SATURATION) => Command { color: Some(Hsb { saturation: Some(number? / 100.0), ..Hsb::default() }), ..Command::default() },
        (Role::Main, BRIGHTNESS) => Command { color: Some(Hsb { brightness: Some(number? / 100.0), ..Hsb::default() }), ..Command::default() },
        // switching "Up" off stops the window
        (Role::Up, ON) => Command { direction: value.as_bool()?.then_some(Direction::Up), ..Command::default() },
        (Role::Down, ON) => Command { direction: value.as_bool()?.then_some(Direction::Down), ..Command::default() },
        _ => return None,
    })
}

pub async fn serve(home: Arc<Home>, data: PathBuf, simulated: bool) {
    let name = if simulated { "RdvTest" } else { "RdvHome" };
    let bindings = Arc::new(bindings(&home));
    let (hap, mut written) = Hap::new(name, PORT, State::load(state_file(data)), accessories(name, &bindings));
    let _ = RUNNING.set(hap.clone());

    println!("Setup payload: {}\nOr enter this code in your HomeKit app on your iOS device: {}", hap.setup_uri(), hap.pincode());

    // the house -> homekit
    let mut events = home.subscribe();
    let (publisher, published) = (hap.clone(), bindings.clone());
    tokio::spawn(async move {
        loop {
            match events.recv().await {
                Ok(event) => {
                    for binding in published.iter().filter(|b| b.switch.id == event.id) {
                        publish(&publisher, binding, &event.report);
                    }
                }
                Err(RecvError::Lagged(_)) => continue,
                Err(RecvError::Closed) => break,
            }
        }
    });

    // homekit -> the house
    tokio::spawn(async move {
        while let Some((aid, iid, value)) = written.recv().await {
            let Some(binding) = bindings.iter().find(|b| b.aid == aid) else { continue };

            if let Some(cmd) = command(binding.role, iid, &value) {
                println!("Homekit -> {} {:?}", binding.switch.id, cmd);
                let switch = binding.switch.clone();
                tokio::spawn(async move { switch.apply(&cmd).await });
            }
        }
    });

    // the values to start with
    let everything = home.filter(None);
    tokio::spawn(async move { Home::status(&everything).await });

    if let Err(e) = hap.serve().await {
        eprintln!("homekit: {}", e);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sha2::{Digest, Sha512};

    // GET /accessories of the old app (hap-python 5.0.0, DEBUG, never switched) and
    // the hash it wrote in accessory.state: ours must be the same, id by id.
    #[test]
    fn same_accessories_as_hap_python() {
        std::env::set_var("RDV_DATA_DIR", std::env::temp_dir().join("rdvhome-test"));

        let (home, _) = crate::home::build();
        let ours: Vec<Value> = accessories("RdvTest", &bindings(&home)).iter().map(|a| a.to_json(true)).collect();
        let theirs: Value = serde_json::from_str(include_str!("hap/fixtures/hap-python-accessories.json")).unwrap();

        assert_eq!(json!({"accessories": ours}), theirs);

        let without_values: Vec<Value> = accessories("RdvTest", &bindings(&home)).iter().map(|a| a.to_json(false)).collect();
        let canonical = crate::hap::accessory::sorted(&json!({"accessories": without_values})).to_string();
        let hash: String = Sha512::digest(canonical.as_bytes()).iter().map(|b| format!("{:02x}", b)).collect();

        assert!(hash.starts_with("82ca6f10f77c922a309cce0db524e54746a38834"), "{}", hash);
    }
}
