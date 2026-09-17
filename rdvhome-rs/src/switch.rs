// Switch is what the api talks about: an id, a name, an icon, aliases... around
// one Device. Home is the list of them. Everything a switch reads or does goes
// out as an event, and the websockets (and homekit) listen to all of them.

use std::sync::Arc;

use futures_util::future::join_all;
use serde_json::{json, Map, Value};
use tokio::sync::broadcast;

use crate::device::hue::number;
use crate::device::{changed, ColorReport, Command, Device, Report};
use crate::json::dumps;

#[derive(Clone)]
pub struct Event {
    pub id: String,
    pub report: Report,
    // the json the websockets send
    pub text: Arc<String>,
}

pub struct Switch {
    pub id: String,
    pub name: String,
    pub kind: &'static str,
    pub icon: String,
    pub alias: Vec<String>,
    pub ordering: usize,
    pub zone: Option<String>,
    pub room: Option<String>,
    pub device: Arc<dyn Device>,
    events: broadcast::Sender<Event>,
}

impl Switch {
    pub fn serialize(&self, report: &Report) -> Map<String, Value> {
        let mut out = Map::new();
        let capabilities = self.device.capabilities();

        out.insert("id".into(), json!(self.id));

        if report.full {
            out.insert("name".into(), json!(self.name));
            out.insert("kind".into(), json!(self.kind));
            out.insert("icon".into(), json!(self.icon));
            out.insert("alias".into(), json!(self.alias));
            out.insert("ordering".into(), json!(self.ordering));
            out.insert("zone".into(), json!(self.zone));
            out.insert("room".into(), json!(self.room));
            out.insert("allow_on".into(), json!(capabilities.on));
            out.insert("allow_hue".into(), json!(capabilities.hue));
            out.insert("allow_saturation".into(), json!(capabilities.saturation));
            out.insert("allow_brightness".into(), json!(capabilities.brightness));
            out.insert("allow_direction".into(), json!(capabilities.direction));
            out.insert("allow_visibility".into(), json!(capabilities.visibility));
            out.insert(
                "effects".into(),
                Value::Object(self.device.effects().iter().map(|e| (e.clone(), json!(e))).collect()),
            );
        }

        if let Some(on) = report.on {
            out.insert("on".into(), json!(on));
            out.insert("off".into(), json!(!on));
        }

        if let Some(allow_on) = report.allow_on {
            out.insert("allow_on".into(), json!(allow_on));
        }

        // the two orders are the ones of the old app
        match &report.color {
            Some(ColorReport::Stored { hue, brightness, saturation }) => {
                out.insert("hue".into(), json!(hue));
                out.insert("brightness".into(), json!(brightness));
                out.insert("saturation".into(), json!(saturation));
            }
            Some(ColorReport::Applied(color)) => {
                for (key, value) in [("hue", color.hue), ("saturation", color.saturation), ("brightness", color.brightness)] {
                    if let Some(value) = value {
                        out.insert(key.into(), json!(number(value)));
                    }
                }
            }
            None => {}
        }

        if let Some(effect) = &report.effect {
            out.insert("effect".into(), json!(effect));
        }

        if let Some((up, down)) = report.moving {
            out.insert("up".into(), json!(up));
            out.insert("down".into(), json!(down));
        }

        out
    }

    fn send(&self, report: Report) -> Value {
        let value = Value::Object(self.serialize(&report));
        let _ = self.events.send(Event { id: self.id.clone(), report, text: Arc::new(dumps(&value)) });
        value
    }

    pub async fn status(&self) -> Value {
        self.send(self.device.read().await)
    }

    pub async fn apply(&self, cmd: &Command) -> Value {
        self.send(self.device.apply(cmd).await)
    }
}

pub struct Description<'a> {
    pub id: &'a str,
    pub name: &'a str,
    pub icon: &'a str,
    pub alias: &'a [&'a str],
    pub zone: Option<&'a str>,
    pub room: Option<&'a str>,
}

pub struct Home {
    pub switches: Vec<Arc<Switch>>,
    events: broadcast::Sender<Event>,
}

pub struct HomeBuilder {
    switches: Vec<Arc<Switch>>,
    events: broadcast::Sender<Event>,
}

impl HomeBuilder {
    pub fn new() -> HomeBuilder {
        HomeBuilder { switches: Vec::new(), events: broadcast::channel(1024).0 }
    }

    // every switch answers to its id, its aliases, "all" (not the scenes) and its kind
    pub fn add(&mut self, kind: &'static str, description: Description, device: Arc<dyn Device>) {
        let mut alias = vec![description.id.to_string()];
        alias.extend(description.alias.iter().map(|a| a.to_string()));
        if kind == "switch" {
            alias.push("all".to_string());
        }
        alias.push(kind.to_string());

        self.switches.push(Arc::new(Switch {
            id: description.id.to_string(),
            name: description.name.to_string(),
            kind,
            icon: description.icon.to_string(),
            alias,
            ordering: self.switches.len() + 1,
            zone: description.zone.map(String::from),
            room: description.room.map(String::from),
            device,
            events: self.events.clone(),
        }));
    }

    pub fn build(self) -> Arc<Home> {
        Arc::new(Home { switches: self.switches, events: self.events })
    }
}

impl Home {
    pub fn subscribe(&self) -> broadcast::Receiver<Event> {
        self.events.subscribe()
    }

    // None is everything
    pub fn filter(&self, alias: Option<&str>) -> Vec<Arc<Switch>> {
        self.switches.iter().filter(|s| alias.is_none_or(|a| s.alias.iter().any(|x| x == a))).cloned().collect()
    }

    pub fn filter_any(&self, aliases: &[String]) -> Vec<Arc<Switch>> {
        self.switches.iter().filter(|s| aliases.iter().any(|a| s.alias.contains(a))).cloned().collect()
    }

    pub async fn status(switches: &[Arc<Switch>]) -> Map<String, Value> {
        let values = join_all(switches.iter().map(|s| s.status())).await;
        switches.iter().map(|s| s.id.clone()).zip(values).collect()
    }

    pub async fn apply(switches: &[Arc<Switch>], cmd: &Command) -> Map<String, Value> {
        let values = join_all(switches.iter().map(|s| s.apply(cmd))).await;
        switches.iter().map(|s| s.id.clone()).zip(values).collect()
    }

    // background loops, and a status event whenever a device says it changed
    pub fn start(self: &Arc<Self>) {
        for switch in &self.switches {
            switch.device.clone().start();

            if let Some(mut source) = switch.device.changes() {
                let switch = switch.clone();

                tokio::spawn(async move {
                    while changed(&mut source).await {
                        switch.status().await;
                    }
                });
            }
        }
    }
}
