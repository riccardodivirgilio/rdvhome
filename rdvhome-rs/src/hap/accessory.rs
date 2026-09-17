// The accessory database: what GET /accessories answers. Ids are given in
// order like hap-python does (services and characteristics count from 1 inside
// every accessory), because the controllers remember them: same ids, same
// json, same hash, and an iPhone paired with the old app sees no change.

use serde_json::{json, Map, Value};

#[derive(Clone, Copy, PartialEq)]
pub enum Format {
    Bool,
    Int,
    Float,
    Text,
}

pub struct Characteristic {
    pub iid: u64,
    kind: &'static str,
    perms: &'static [&'static str],
    pub format: Format,
    // minValue, minStep, unit, maxValue
    range: Option<(f64, f64, &'static str, f64)>,
    pub value: Option<Value>,
}

impl Characteristic {
    pub fn can(&self, permission: &str) -> bool {
        self.perms.contains(&permission)
    }

    // what hap-python's to_valid_value does: snap to the step, clamp, cast
    pub fn valid(&self, value: &Value) -> Option<Value> {
        match self.format {
            Format::Bool => Some(json!(value.as_bool().or_else(|| value.as_f64().map(|v| v != 0.0))?)),
            Format::Text => Some(json!(value.as_str()?.chars().take(64).collect::<String>())),
            Format::Int | Format::Float => {
                let mut number = value.as_f64().or_else(|| value.as_bool().map(|b| b as u8 as f64))?;

                if let Some((min, step, _, max)) = self.range {
                    number = ((number / step).round() * step).clamp(min, max);
                }

                Some(if self.format == Format::Int { json!(number as i64) } else { json!(number) })
            }
        }
    }

    fn to_json(&self, with_value: bool) -> Value {
        let mut out = Map::new();
        let whole = |v: f64| json!(v as i64);

        out.insert("iid".into(), json!(self.iid));
        out.insert("type".into(), json!(self.kind));
        out.insert("perms".into(), json!(self.perms));
        out.insert(
            "format".into(),
            json!(match self.format {
                Format::Bool => "bool",
                Format::Int => "int",
                Format::Float => "float",
                Format::Text => "string",
            }),
        );

        if let Some((min, step, unit, max)) = self.range {
            out.insert("minValue".into(), whole(min));
            out.insert("minStep".into(), whole(step));
            out.insert("unit".into(), json!(unit));
            out.insert("maxValue".into(), whole(max));
        }

        if let (true, Some(value)) = (with_value && self.can("pr"), &self.value) {
            out.insert("value".into(), value.clone());
        }

        Value::Object(out)
    }
}

pub struct Service {
    iid: u64,
    kind: &'static str,
    pub characteristics: Vec<Characteristic>,
}

pub struct Accessory {
    pub aid: u64,
    pub services: Vec<Service>,
}

pub enum Kind {
    Bridge,
    Switch,
    // with hue, saturation and brightness or just on / off
    Lightbulb { color: bool },
}

pub const ON: u64 = 9;
pub const HUE: u64 = 10;
pub const SATURATION: u64 = 11;
pub const BRIGHTNESS: u64 = 12;

const READ: &[&str] = &["pr"];
const READ_NOTIFY: &[&str] = &["pr", "ev"];
const READ_WRITE_NOTIFY: &[&str] = &["pr", "pw", "ev"];

type Range = Option<(f64, f64, &'static str, f64)>;

// ids count from 1 inside every accessory, services and characteristics together
struct Ids(u64);

impl Ids {
    fn next(&mut self) -> u64 {
        self.0 += 1;
        self.0
    }

    fn characteristic(&mut self, kind: &'static str, perms: &'static [&'static str], format: Format, range: Range, value: Option<Value>) -> Characteristic {
        Characteristic { iid: self.next(), kind, perms, format, range, value }
    }

    fn on(&mut self) -> Characteristic {
        self.characteristic("25", READ_WRITE_NOTIFY, Format::Bool, None, Some(json!(false)))
    }
}

impl Accessory {
    pub fn new(aid: u64, name: &str, kind: Kind) -> Accessory {
        let mut ids = Ids(0);
        let text = |value: &str| Some(json!(value));

        // AccessoryInformation: identify, manufacturer, model, name, serial number, firmware revision
        let information = Service {
            iid: ids.next(),
            kind: "3E",
            characteristics: vec![
                ids.characteristic("14", &["pw"], Format::Bool, None, None),
                ids.characteristic("20", READ, Format::Text, None, text("")),
                ids.characteristic("21", READ, Format::Text, None, text("")),
                ids.characteristic("23", READ, Format::Text, None, text(name)),
                ids.characteristic("30", READ, Format::Text, None, text("default")),
                ids.characteristic("52", READ, Format::Text, None, text("")),
            ],
        };

        let iid = ids.next();
        let service = match kind {
            // HAPProtocolInformation: version
            Kind::Bridge => Service {
                iid,
                kind: "A2",
                characteristics: vec![ids.characteristic("37", READ_NOTIFY, Format::Text, None, text("01.01.00"))],
            },
            Kind::Switch => Service { iid, kind: "49", characteristics: vec![ids.on()] },
            Kind::Lightbulb { color } => {
                let mut characteristics = vec![ids.on()];

                if color {
                    characteristics.extend([
                        ids.characteristic("13", READ_WRITE_NOTIFY, Format::Float, Some((0.0, 1.0, "arcdegrees", 360.0)), Some(json!(0))),
                        ids.characteristic("2F", READ_WRITE_NOTIFY, Format::Float, Some((0.0, 1.0, "percentage", 100.0)), Some(json!(0))),
                        ids.characteristic("8", READ_WRITE_NOTIFY, Format::Int, Some((0.0, 1.0, "percentage", 100.0)), Some(json!(0))),
                    ]);
                }

                Service { iid, kind: "43", characteristics }
            }
        };

        Accessory { aid, services: vec![information, service] }
    }

    pub fn characteristic(&mut self, iid: u64) -> Option<&mut Characteristic> {
        self.services.iter_mut().flat_map(|s| s.characteristics.iter_mut()).find(|c| c.iid == iid)
    }

    pub fn to_json(&self, with_values: bool) -> Value {
        let services: Vec<Value> = self
            .services
            .iter()
            .map(|service| {
                let characteristics: Vec<Value> = service.characteristics.iter().map(|c| c.to_json(with_values)).collect();
                json!({"iid": service.iid, "type": service.kind, "characteristics": characteristics})
            })
            .collect();

        json!({"aid": self.aid, "services": services})
    }
}

// keys sorted at every level, compact: what hap-python hashes
pub fn sorted(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            Value::Object(keys.into_iter().map(|k| (k.clone(), sorted(&map[k]))).collect())
        }
        Value::Array(items) => Value::Array(items.iter().map(sorted).collect()),
        other => other.clone(),
    }
}
