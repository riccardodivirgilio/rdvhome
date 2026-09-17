// In-memory Philips Hue bridge, seeded from captures/get-lights.http.
//
//   GET /api/<any>/lights/           -> all lights
//   GET /api/<any>/lights/<id>       -> one light
//   PUT /api/<any>/lights/<id>/state -> validated, then merged into the light state
//
// Validation mimics what the real bridge answered (see captures/invalid-*.http):
// always 200, with a list of {"error": ...} (first) and {"success": ...} items.
//   2   body contains invalid json
//   3   resource not available (unknown light)
//   6   parameter not available (unknown, read only, or missing on this light: hue on a plug)
//   7   invalid value
//   201 parameter not modifiable while the light is off (everything but on and bri)
// Out of range bri / sat / ct are clamped, like the bridge does for bri.
// Not supported: *_inc parameters (answered as 6).

use serde_json::{json, Map, Value};

use crate::{body, lookup, with_body, Capture};

pub struct State {
    lights: Value,
}

impl State {
    pub fn new(captures: &[Capture]) -> State {
        let lights = captures
            .iter()
            .find(|c| c.method == "GET" && c.path.ends_with("/lights/"))
            .and_then(|c| serde_json::from_slice(body(&c.response)).ok())
            .unwrap_or_else(|| json!({}));

        State { lights }
    }

    pub fn handle(
        &mut self,
        captures: &[Capture],
        method: &str,
        path: &str,
        payload: &[u8],
    ) -> Option<Vec<u8>> {
        // ["", "api", token, "lights", id, "state"]
        let segments: Vec<&str> = path.split('?').next()?.split('/').collect();

        if segments.get(1) != Some(&"api") || segments.get(3) != Some(&"lights") {
            return None;
        }

        let id = segments.get(4).copied().unwrap_or("");

        let result = match (method, segments.len()) {
            ("GET", 4) => self.lights.clone(),
            ("GET", 5) if id.is_empty() => self.lights.clone(),
            ("GET", 5) => match self.lights.get(id) {
                Some(light) => light.clone(),
                None => error(3, &format!("/lights/{}", id), None),
            },
            ("PUT", 6) if segments[5] == "state" => self.update(id, payload),
            _ => return None,
        };

        // headers of the captured response for the same kind of request
        let capture = lookup(captures, method, path, payload)
            .or_else(|| captures.iter().find(|c| c.method == method))?;

        Some(with_body(&capture.response, result.to_string().as_bytes()))
    }

    fn update(&mut self, id: &str, payload: &[u8]) -> Value {
        let address = format!("/lights/{}/state", id);

        let Some(state) = self.lights.get_mut(id).and_then(|light| light.get_mut("state")) else {
            return error(3, &address, None);
        };

        let Ok(changes) = serde_json::from_slice::<Map<String, Value>>(payload) else {
            return error(2, &address, None);
        };

        // "on" in the same request counts: {"on": true, "hue": 0} works on a light that is off
        let is_on = match changes.get("on") {
            Some(Value::Bool(on)) => *on,
            _ => state["on"] == json!(true),
        };

        let mut errors = Vec::new();
        let mut successes = Vec::new();

        for (key, value) in changes {
            let address = format!("{}/{}", address, key);

            let available = key == "transitiontime"
                || (state.get(&key).is_some() && !["colormode", "mode", "reachable"].contains(&key.as_str()));

            if !available {
                errors.push(error(6, &address, Some(&key)));
                continue;
            }

            let Some(value) = validate(&key, &value) else {
                // the bridge really prints it like this: `invalid value, 70000}, for parameter, hue`
                let printed = value.to_string().replace('"', " ");
                errors.push(json!({"error": {
                    "type": 7,
                    "address": address,
                    "description": format!("invalid value, {}}}, for parameter, {}", printed, key),
                }}));
                continue;
            };

            if !is_on && key != "on" && key != "bri" {
                errors.push(error(201, &address, Some(&key)));
                continue;
            }

            match key.as_str() {
                "hue" | "sat" => state["colormode"] = json!("hs"),
                "xy" => state["colormode"] = json!("xy"),
                "ct" => state["colormode"] = json!("ct"),
                _ => {}
            }

            if key != "transitiontime" {
                state[key.as_str()] = value.clone();
            }

            successes.push(json!({"success": {address: value}}));
        }

        errors.extend(successes);
        Value::Array(errors)
    }
}

// the value to store (clamped when needed), None when invalid
fn validate(key: &str, value: &Value) -> Option<Value> {
    let integer = |min: i64, max: i64| value.as_i64().filter(|v| (min..=max).contains(v));

    match key {
        "on" => value.as_bool().map(Value::from),
        "bri" => integer(0, 255).map(|v| json!(v.clamp(1, 254))),
        "sat" => integer(0, 255).map(|v| json!(v.min(254))),
        "hue" => integer(0, 65535).map(Value::from),
        "ct" => integer(0, 65535).map(|v| json!(v.clamp(153, 500))),
        "transitiontime" => integer(0, 65535).map(Value::from),
        "effect" => value.as_str().filter(|v| ["none", "colorloop"].contains(v)).map(Value::from),
        "alert" => value.as_str().filter(|v| ["none", "select", "lselect"].contains(v)).map(Value::from),
        "xy" => value
            .as_array()
            .filter(|xy| xy.len() == 2 && xy.iter().all(|v| v.as_f64().map_or(false, |v| (0.0..=1.0).contains(&v))))
            .map(|_| value.clone()),
        _ => None,
    }
}

fn error(kind: u32, address: &str, parameter: Option<&str>) -> Value {
    let description = match (kind, parameter) {
        (2, _) => "body contains invalid json".to_string(),
        (6, Some(parameter)) => format!("parameter, {}, not available", parameter),
        (201, Some(parameter)) => format!("parameter, {}, is not modifiable. Device is set to off.", parameter),
        _ => format!("resource, {}, not available", address),
    };

    let item = json!({"error": {"type": kind, "address": address, "description": description}});

    // single errors are the whole response, the others are collected in a list
    if parameter.is_some() { item } else { json!([item]) }
}
