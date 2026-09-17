// In-memory Nanoleaf panels, one per captured token (pc, exa), seeded from
// captures/*-get-state.http, *-get-effects-select.http and *-get-effects-list.http.
// An unknown token gets the first device.
//
//   GET /api/v1/<token>                     -> everything (captured info + current state/effects)
//   GET /api/v1/<token>/state               -> state
//   GET /api/v1/<token>/state/<key>         -> one attribute
//   GET /api/v1/<token>/effects/select      -> running effect
//   GET /api/v1/<token>/effects/effectsList -> installed effects
//   PUT /api/v1/<token>/state               -> merged into the state (204)
//   PUT /api/v1/<token>/effects             -> select (204, unknown 400) / write (204)
//
// Validation mimics what the real panels answered (see captures/*-invalid-*.http),
// always with an empty body:
//   422 invalid json
//   404 unknown state attribute, unknown path
//   400 wrong type / shape, value outside min..max, unknown effect or command
//   {}  the real device answers with a broken response without status line, so do we
// Values must be integers ({"value": n}, or {"increment": n}), "on" a boolean.

use serde_json::{json, Map, Value};

use crate::{body, lookup, with_body, Capture};

const NO_CONTENT: &[u8] = b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n";
const BAD_REQUEST: &[u8] = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n";
const NOT_FOUND: &[u8] = b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n";
const UNPROCESSABLE: &[u8] = b"HTTP/1.1 422 Unprocessable Entity\r\nContent-Length: 0\r\n\r\n";
const BROKEN: &[u8] = b"\r\nContent-Length: 0\r\n\r\n";

struct Device {
    token: String,
    info: Value,
    state: Value,
    effect: Value,
    effects: Value,
}

pub struct State {
    devices: Vec<Device>,
}

// ["", "api", "v1", token, ...rest]
fn split(path: &str) -> Option<(&str, String)> {
    let segments: Vec<&str> = path.split('?').next()?.split('/').collect();

    if segments.len() < 4 || segments[1] != "api" || segments[2] != "v1" {
        return None;
    }

    Some((segments[3], segments[4..].join("/")))
}

impl State {
    pub fn new(captures: &[Capture]) -> State {
        let mut devices: Vec<Device> = Vec::new();

        for capture in captures.iter().filter(|c| c.method == "GET") {
            let Some((token, rest)) = split(&capture.path) else { continue };
            let Ok(value) = serde_json::from_slice::<Value>(body(&capture.response)) else { continue };

            let index = match devices.iter().position(|d| d.token == token) {
                Some(index) => index,
                None => {
                    devices.push(Device {
                        token: token.to_string(),
                        info: json!({}),
                        state: json!({}),
                        effect: json!("*Solid*"),
                        effects: json!([]),
                    });
                    devices.len() - 1
                }
            };
            let device = &mut devices[index];

            // first capture wins, like the static lookup
            match rest.as_str() {
                "" => device.info = value,
                "state" if device.state == json!({}) => device.state = value,
                "effects/select" if device.effect == json!("*Solid*") => device.effect = value,
                "effects/effectsList" if device.effects == json!([]) => device.effects = value,
                _ => {}
            }
        }

        for device in &devices {
            println!("device {}: {} effects, running {}", device.token, device.effects.as_array().map_or(0, |e| e.len()), device.effect);
        }

        State { devices }
    }

    pub fn handle(
        &mut self,
        captures: &[Capture],
        method: &str,
        path: &str,
        payload: &[u8],
    ) -> Option<Vec<u8>> {
        let (token, rest) = split(path)?;

        let index = self.devices.iter().position(|d| d.token == token).unwrap_or(0);
        let device = self.devices.get_mut(index)?;

        let result = match (method, rest.as_str()) {
            ("GET", "") => device.all(),
            ("GET", "state") => device.state.clone(),
            ("GET", "effects/select") => device.effect.clone(),
            ("GET", "effects/effectsList") => device.effects.clone(),
            ("PUT", "state") => return Some(device.update(payload).to_vec()),
            ("PUT", "effects") => return Some(device.update_effect(payload).to_vec()),
            ("GET", rest) => match rest.strip_prefix("state/").and_then(|key| device.state.get(key)) {
                Some(attribute) => attribute.clone(),
                None => return Some(NOT_FOUND.to_vec()),
            },
            _ => return Some(NOT_FOUND.to_vec()),
        };

        // captured status line + headers of the same kind of request
        let Some(capture) = lookup(captures, method, path, payload)
            .or_else(|| captures.iter().find(|c| c.method == "GET" && c.path.ends_with("/state")))
        else {
            return None;
        };

        Some(with_body(&capture.response, result.to_string().as_bytes()))
    }
}

impl Device {
    fn all(&self) -> Value {
        let mut info = self.info.clone();
        info["state"] = self.state.clone();
        info["effects"] = json!({"effectsList": self.effects, "select": self.effect});
        info
    }

    fn update(&mut self, payload: &[u8]) -> &'static [u8] {
        let Ok(changes) = serde_json::from_slice::<Map<String, Value>>(payload) else {
            return match serde_json::from_slice::<Value>(payload) {
                Ok(_) => BAD_REQUEST,
                Err(_) => UNPROCESSABLE,
            };
        };

        if changes.is_empty() {
            return BROKEN;
        }

        // validate everything first: a refused request changes nothing
        let mut values = Vec::new();

        for (key, change) in &changes {
            let Some(current) = self.state.get(key).filter(|_| key != "colorMode") else {
                return NOT_FOUND;
            };

            let value = if key == "on" {
                change.get("value").filter(|v| v.is_boolean()).cloned()
            } else {
                let (min, max) = (current["min"].as_i64().unwrap_or(0), current["max"].as_i64().unwrap_or(0));
                let integer = |name: &str| change.get(name).and_then(Value::as_i64);

                match (integer("value"), integer("increment")) {
                    (Some(value), _) => Some(value).filter(|v| (min..=max).contains(v)).map(Value::from),
                    (_, Some(increment)) => {
                        Some(json!((current["value"].as_i64().unwrap_or(0) + increment).clamp(min, max)))
                    }
                    _ => None,
                }
            };

            match value {
                Some(value) => values.push((key.as_str(), value)),
                None => return BAD_REQUEST,
            }
        }

        for (key, value) in values {
            match key {
                // a colour leaves the panel in solid mode
                "hue" | "sat" => {
                    self.state["colorMode"] = json!("hs");
                    self.effect = json!("*Solid*");
                }
                "ct" => {
                    self.state["colorMode"] = json!("ct");
                    self.effect = json!("*Solid*");
                }
                _ => {}
            }

            self.state[key]["value"] = value;
        }

        NO_CONTENT
    }

    fn update_effect(&mut self, payload: &[u8]) -> &'static [u8] {
        let Ok(request) = serde_json::from_slice::<Map<String, Value>>(payload) else {
            return match serde_json::from_slice::<Value>(payload) {
                Ok(_) => BAD_REQUEST,
                Err(_) => UNPROCESSABLE,
            };
        };

        if request.is_empty() {
            return BROKEN;
        }

        if let Some(name) = request.get("select") {
            let installed = self.effects.as_array().map_or(false, |e| e.contains(name));

            if !installed {
                return BAD_REQUEST;
            }

            self.effect = name.clone();
        } else if let Some(write) = request.get("write") {
            // only what the app uses: a temporary animation
            if write.get("command") != Some(&json!("display")) || !write["animType"].is_string() {
                return BAD_REQUEST;
            }

            self.effect = json!("*Dynamic*");
        } else {
            return BAD_REQUEST;
        }

        self.state["colorMode"] = json!("effect");
        self.state["on"]["value"] = json!(true);

        NO_CONTENT
    }
}
