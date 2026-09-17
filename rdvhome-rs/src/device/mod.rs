// A Device is one physical thing (a relay, a bulb, a panel, a motor). It knows
// how to read itself, how to obey a command and how to say "I changed". It
// knows nothing about ids, names, json or the other devices: that is Switch.
//
// Devices compose: Powered(relay, bulb) is again a Device.

pub mod hue;
pub mod nanoleaf;
pub mod powered;
pub mod relay;
pub mod scene;
pub mod tv;
pub mod window;

use std::sync::Arc;

use async_trait::async_trait;
use serde_json::Number;
use tokio::sync::broadcast;

use crate::color::Hsb;

#[derive(Clone, Debug)]
pub enum Effect {
    // an effect installed on the panel
    Named(String),
    // a temporary animation around a colour
    Highlight(Hsb),
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Direction {
    Up,
    Down,
}

// What a request asks for. Every device takes what it understands and ignores
// the rest, so one command can go to a whole alias ("all", "default").
#[derive(Clone, Debug, Default)]
pub struct Command {
    pub on: Option<bool>,
    pub color: Option<Hsb>,
    pub effect: Option<Effect>,
    // None is "stop"
    pub direction: Option<Direction>,
}

impl Command {
    pub fn on(on: bool) -> Command {
        Command { on: Some(on), ..Command::default() }
    }
}

#[derive(Clone, Copy, Debug, Default)]
pub struct Capabilities {
    pub on: bool,
    pub hue: bool,
    pub saturation: bool,
    pub brightness: bool,
    pub direction: bool,
    pub visibility: bool,
}

impl Capabilities {
    pub const NONE: Capabilities =
        Capabilities { on: false, hue: false, saturation: false, brightness: false, direction: false, visibility: true };
    pub const ON: Capabilities = Capabilities { on: true, ..Capabilities::NONE };
    pub const COLOR: Capabilities = Capabilities { on: true, hue: true, saturation: true, brightness: true, ..Capabilities::NONE };
}

#[derive(Clone, Debug)]
pub enum ColorReport {
    // what the device has: all three, numbers as they are stored
    Stored { hue: Number, brightness: Number, saturation: Number },
    // what a command asked for: only the components it named
    Applied(Hsb),
}

// What a device says about itself after read() or apply(). `full` asks Switch
// to send the whole description (name, icon, capabilities...) with it.
#[derive(Clone, Debug, Default)]
pub struct Report {
    pub full: bool,
    pub on: Option<bool>,
    // overrides the capability: a bulb without mains cannot be switched on
    pub allow_on: Option<bool>,
    pub color: Option<ColorReport>,
    // Some(None) is "no effect running"
    pub effect: Option<Option<String>>,
    // (up, down)
    pub moving: Option<(bool, bool)>,
}

impl Report {
    pub fn full() -> Report {
        Report { full: true, ..Report::default() }
    }

    // lights answer a command with just what was asked
    pub fn echo(cmd: &Command) -> Report {
        Report { on: cmd.on, color: cmd.color.map(ColorReport::Applied), ..Report::default() }
    }
}

// "something changed, read me again"
pub type Changes = broadcast::Sender<()>;

pub fn changes() -> Changes {
    broadcast::channel(16).0
}

// One connection per request, like the old app: the hue bridge closes them
// anyway and a stale pooled connection would fail the next request.
pub fn http_client() -> reqwest::Client {
    reqwest::Client::builder().pool_max_idle_per_host(0).timeout(std::time::Duration::from_secs(10)).build().expect("http client")
}

// false when the device is gone
pub async fn changed(source: &mut broadcast::Receiver<()>) -> bool {
    !matches!(source.recv().await, Err(broadcast::error::RecvError::Closed))
}

#[async_trait]
pub trait Device: Send + Sync + 'static {
    fn capabilities(&self) -> Capabilities;

    // selectable effects, by name
    fn effects(&self) -> &[String] {
        &[]
    }

    async fn read(&self) -> Report;

    async fn apply(&self, cmd: &Command) -> Report;

    // what the user sees, used by the scenes to skip what is off
    async fn is_on(&self) -> bool {
        false
    }

    // fires when the device changed on its own (wall switch, hue app, timer)
    fn changes(&self) -> Option<broadcast::Receiver<()>> {
        None
    }

    // background loops; must be safe to call more than once (shared devices)
    fn start(self: Arc<Self>) {}
}
