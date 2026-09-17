// Nanoleaf panels. No polling: the state is asked to the panel on every read.

use std::sync::Arc;

use async_trait::async_trait;
use serde_json::{json, Map, Number, Value};

use super::{Capabilities, ColorReport, Command, Device, Effect, Report};
use crate::color::{Hsb, HOMEKIT};

pub struct Nanoleaf {
    client: reqwest::Client,
    // http://<host>:16021/api/v1/<token>
    base: String,
    effects: Vec<String>,
}

impl Nanoleaf {
    pub fn new(host: &str, token: &str, effects: &[&str]) -> Arc<Nanoleaf> {
        Arc::new(Nanoleaf {
            client: crate::device::http_client(),
            base: format!("http://{}:16021/api/v1/{}", host, token),
            effects: effects.iter().map(|e| e.to_string()).collect(),
        })
    }

    async fn get(&self, path: &str) -> Value {
        let response = match self.client.get(format!("{}{}", self.base, path)).send().await {
            Ok(response) => response.json().await,
            Err(e) => Err(e),
        };

        response.unwrap_or_else(|e| {
            eprintln!("nanoleaf: {}", e);
            Value::Null
        })
    }

    // writes are answered with an empty 204 (an empty 400 when refused)
    async fn put(&self, path: &str, payload: Value) {
        if let Err(e) = self.client.put(format!("{}{}", self.base, path)).json(&payload).send().await {
            eprintln!("nanoleaf: {}", e);
        }
    }
}

// {"value": 120, "max": 360, "min": 0} -> 0.333
fn ratio(attribute: &Value) -> Number {
    let value = attribute["value"].as_f64().unwrap_or(0.0) / attribute["max"].as_f64().unwrap_or(1.0);
    Number::from_f64(value).unwrap_or_else(|| Number::from(0))
}

#[async_trait]
impl Device for Nanoleaf {
    fn capabilities(&self) -> Capabilities {
        Capabilities::COLOR
    }

    fn effects(&self) -> &[String] {
        &self.effects
    }

    async fn read(&self) -> Report {
        let state = self.get("/state").await;
        let effect = self.get("/effects/select").await;

        Report {
            on: Some(state["on"]["value"].as_bool().unwrap_or(false)),
            allow_on: Some(true),
            color: Some(ColorReport::Stored {
                hue: ratio(&state["hue"]),
                brightness: ratio(&state["brightness"]),
                saturation: ratio(&state["sat"]),
            }),
            // *Solid*, *Dynamic* and effects picked in the nanoleaf app are not ours
            effect: Some(effect.as_str().filter(|e| self.effects.iter().any(|known| known == e)).map(String::from)),
            ..Report::full()
        }
    }

    async fn apply(&self, cmd: &Command) -> Report {
        let color = cmd.color.map(ColorReport::Applied);

        match &cmd.effect {
            // the scenes send the same effect to every panel, and every panel
            // has a different set: not having it is not an error
            Some(Effect::Named(name)) if !self.effects.is_empty() && !self.effects.contains(name) => Report::full(),

            Some(Effect::Named(name)) => {
                self.put("/effects", json!({"select": name})).await;

                Report { on: Some(true), color, effect: Some(Some(name.clone())), ..Report::full() }
            }

            Some(Effect::Highlight(around)) => {
                let palette: Vec<Value> = (1..=3)
                    .map(|i| {
                        let [hue, saturation, brightness] = Hsb {
                            hue: around.hue,
                            saturation: around.saturation.map(|s| s / i as f64),
                            brightness: Some(1.0),
                        }
                        .scaled(HOMEKIT);

                        let mut entry = Map::new();
                        for (key, value) in [("hue", hue), ("saturation", saturation), ("brightness", brightness)] {
                            if let Some(value) = value {
                                entry.insert(key.into(), json!(value));
                            }
                        }
                        Value::Object(entry)
                    })
                    .collect();

                self.put(
                    "/effects",
                    json!({"write": {
                        "command": "display",
                        "animName": "New animation",
                        "animType": "highlight",
                        "colorType": "HSB",
                        "animData": null,
                        "palette": palette,
                        "brightnessRange": {"minValue": 50, "maxValue": 100},
                        "transTime": {"minValue": 5, "maxValue": 10},
                        "delayTime": {"minValue": 5, "maxValue": 10},
                        "loop": true,
                    }}),
                )
                .await;

                Report { on: Some(true), color: Some(ColorReport::Applied(*around)), effect: Some(None), ..Report::full() }
            }

            None => {
                let mut request = Map::new();

                if let Some(on) = cmd.on {
                    request.insert("on".into(), json!({"value": on}));
                }

                // a colour would switch the panel on again
                if let (Some(color), true) = (&cmd.color, cmd.on != Some(false)) {
                    for (key, value) in ["hue", "sat", "brightness"].into_iter().zip(color.scaled(HOMEKIT)) {
                        if let Some(value) = value {
                            request.insert(key.into(), json!({"value": value}));
                        }
                    }
                }

                // nothing to say (a "stop" sent to everything): an empty put makes the panel answer garbage
                if !request.is_empty() {
                    self.put("/state", Value::Object(request)).await;
                }

                // a colour leaves the panel in solid mode: no effect running
                Report { on: cmd.on, color, effect: Some(None), ..Report::full() }
            }
        }
    }

    async fn is_on(&self) -> bool {
        self.get("/state").await["on"]["value"].as_bool().unwrap_or(false)
    }
}
