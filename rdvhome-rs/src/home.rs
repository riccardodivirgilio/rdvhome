// The house. This is the configuration, as code like run.py was: what is
// wired to which pin, which bulb is which hue id, the scenes.
//
//   RELAY1  6  5  9 13 11 27 22 10     windows: power / direction pairs
//   RELAY2 14 15 18 23 24 16 20 21     lights: pulse toggles the mains
//   INPUT   2  3  4 17 25  8  7 12     status: low when the mains is there

use std::sync::Arc;

use crate::color::Hsb;
use crate::device::hue::{HueBridge, HueLight, HueOptions};
use crate::device::nanoleaf::Nanoleaf;
use crate::device::powered::Powered;
use crate::device::relay::Relay;
use crate::device::scene::{Colors, Effects, Scene, SceneDevice};
use crate::device::tv::Tv;
use crate::device::window::Window;
use crate::device::Device;
use crate::gpio::{self, Gpio};
use crate::homekit::Homekit;
use crate::store::{data_dir, Store};
use crate::switch::{Description, Home, HomeBuilder};

pub const RELAY2: [u8; 8] = [14, 15, 18, 23, 24, 16, 20, 21];

const PHILIPS_TOKEN: &str = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W";
const NANOLEAF_PC_TOKEN: &str = "lWI4Ymlb9WkrELgfnXZBlQyeuXljzaw1";
const NANOLEAF_EXA_TOKEN: &str = "XIp9FxkONwwxGs0jqWGeNrrhOIB76Rtb";

// Hosts of the real devices, docker-compose.yml points them to the mock servers.
fn host(variable: &str, default: &str) -> String {
    std::env::var(variable).unwrap_or_else(|_| default.to_string())
}

struct Builder {
    home: HomeBuilder,
    gpio: Arc<dyn Gpio>,
    bridge: Arc<HueBridge>,
    scenes: Vec<Arc<Scene>>,
}

fn describe<'a>(id: &'a str, name: &'a str, icon: &'a str, alias: &'a [&'a str], zone: Option<&'a str>, room: &'a str) -> Description<'a> {
    // in the Home app: the lights are lightbulbs, the windows two switches, the rest
    // (tv, nanoleaf, scenes) plain switches. Changing this changes what the paired iPhones see.
    let homekit = match id {
        "philips_pool" => Homekit::Hidden,
        "tv" => Homekit::Switch,
        _ if id.starts_with("nanoleaf") => Homekit::Switch,
        _ if id.starts_with("window") => Homekit::Window,
        _ => Homekit::Lightbulb,
    };

    Description { id, name, icon, alias, zone, room: Some(room), homekit }
}

impl Builder {
    fn switch(&mut self, description: Description, device: Arc<dyn Device>) {
        self.home.add("switch", description, device);
    }

    fn hue(&self, key: &str, id: u32) -> Arc<HueLight> {
        self.bridge.light(id, key, HueOptions::default())
    }

    // a hue strip whose mains goes through a relay
    fn strip(&self, key: &str, id: u32, power: &Arc<Relay>) -> Arc<dyn Device> {
        Powered::new(power.clone(), self.bridge.light(id, key, HueOptions { behind_relay: true, ..HueOptions::default() }))
    }

    fn relay(&self, relay: u8, status: u8) -> Arc<Relay> {
        Relay::new(self.gpio.clone(), relay, status)
    }

    fn window(&self, power: u8, direction: u8) -> Arc<Window> {
        Window::new(self.gpio.clone(), power, direction)
    }

    #[allow(clippy::too_many_arguments)]
    fn scene(&mut self, id: &str, name: &str, icon: &str, colors: Colors, effects: Effects, timeout: Option<(f64, f64)>, turn_on: &[&str]) {
        let scene = Scene::new(id, colors, effects, timeout, turn_on);

        self.scenes.push(scene.clone());
        self.home.add(
            "control",
            Description { id, name, icon, alias: &[], zone: None, room: Some("Scene"), homekit: Homekit::Switch },
            Arc::new(SceneDevice(scene)),
        );
    }
}

fn per_panel(tv: &str, exa: &str) -> Effects {
    Effects::PerSwitch(vec![("nanoleaf_tv".into(), tv.into()), ("nanoleaf_exa".into(), exa.into())])
}

fn around(hue: f64, saturation: f64, factor: f64) -> Colors {
    Colors::Perturb { base: Some(Hsb { hue: Some(hue), saturation: Some(saturation), brightness: None }), factor }
}

// the house, and if the pins are simulated (not on the raspberry)
pub fn build() -> (Arc<Home>, bool) {
    let gpio = gpio::open();
    let simulated = gpio.is_simulated();
    let store = Store::new(data_dir(gpio.is_simulated()), "remote");
    let bridge = HueBridge::new(&host("RDV_PHILIPS_GATEWAY_HOST", "philips.impazzito.it"), PHILIPS_TOKEN, store);

    let mut b = Builder { home: HomeBuilder::new(), gpio, bridge: bridge.clone(), scenes: Vec::new() };

    // one relay powers both strips around the tv
    let tv_strips = b.relay(20, 4);

    b.switch(describe("philips_pool", "Philips Pool", "💡", &[], None, "Scene"), bridge);

    let device = b.hue("led_kitchen", 6);
    b.switch(describe("led_kitchen", "Kitchen Led", "🍽", &["default"], Some("Kitchen"), "Living"), device);

    let device = b.relay(24, 17);
    b.switch(describe("spotlight_kitchen", "Kitchen Light", "🍽", &[], Some("Kitchen"), "Living"), device);

    let device = b.relay(23, 2);
    b.switch(describe("spotlight_living_room", "Living Room Light", "🛋", &[], None, "Living"), device);

    let device = b.strip("led_living_room", 1, &tv_strips);
    b.switch(describe("led_living_room", "Living Room Led", "🛋", &["default"], Some("Living Room"), "Living"), device);

    b.switch(describe("tv", "TV", "📺", &[], None, "Living"), Tv::new("192.168.67.235"));

    let device = b.strip("led_tv", 3, &tv_strips);
    b.switch(describe("led_tv", "TV Led", "📺", &["default"], Some("Living Room"), "Living"), device);

    let device = b.relay(15, 25);
    b.switch(describe("spotlight_tv", "TV Light", "📺", &[], None, "Living"), device);

    // the effect names must match the ones installed on the panel exactly
    b.switch(
        describe("nanoleaf_tv", "TV Desk Light", "📺", &["default", "nanoleaf"], None, "Living"),
        Nanoleaf::new(
            &host("RDV_NANOLEAF_PC_HOST", "nanoleaf-pc.impazzito.it"),
            NANOLEAF_PC_TOKEN,
            &[
                "Color Burst", "Fireworks", "Flames", "Forest", "Inner Peace", "Meteor Shower", "Nemo",
                "Northern Lights", "Paint Splatter", "Pulse Pop Beats", "Rhythmic Northern Lights", "Ripple",
                "Romantic", "Snowfall", "Sound Bar", "Streaking Notes",
            ],
        ),
    );
    b.switch(
        describe("nanoleaf_exa", "TV Mirror Light", "📺", &["default", "nanoleaf"], None, "Living"),
        Nanoleaf::new(
            &host("RDV_NANOLEAF_EXA_HOST", "nanoleaf-exa.impazzito.it"),
            NANOLEAF_EXA_TOKEN,
            &[
                "Beatdrop", "Blaze", "Cocoa Beach", "Cotton Candy", "Date Night", "Hip Hop", "Hot Sauce", "Jungle",
                "Lightscape", "Morning Sky", "Northern Lights", "Pop Rocks", "Prism", "Starlight", "Sundown",
                "Waterfall",
            ],
        ),
    );

    let device = b.relay(18, 7);
    b.switch(describe("spotlight_entrance", "Entrance Light", "🚪", &[], None, "Living"), device);

    let device = b.hue("lamp_room", 7);
    b.switch(describe("lamp_room", "Computer lamp", "🖥️", &["default"], Some("Studio"), "Studio"), device);

    let device = b.hue("led_bathroom_entrance", 5);
    b.switch(describe("led_bathroom_entrance", "Bathroom Entrance", "🚽", &[], None, "Bathrooms"), device);

    let power = b.relay(14, 8);
    let device = b.strip("led_bedroom", 2, &power);
    b.switch(describe("led_bedroom", "Bedroom Led", "🛏", &[], Some("Bedroom"), "Bedroom"), device);

    let device = b.relay(21, 3);
    b.switch(describe("spotlight_bedroom", "Bedroom Light", "🛏", &[], None, "Bedroom"), device);

    let device = b.hue("led_bathroom_bedroom", 4);
    b.switch(describe("led_bathroom_bedroom", "Bathroom Bedroom", "🚽", &[], Some("Bathroom"), "Bathrooms"), device);

    let device = b.relay(16, 12);
    b.switch(describe("spotlight_room", "Studio Light", "📚", &[], None, "Studio"), device);

    let device = b.hue("led_room", 8);
    b.switch(describe("led_room", "Studio Led", "💡", &["default"], Some("Studio"), "Studio"), device);

    // a white bulb: no colours
    let device = b.bridge.light(9, "lamp_hipster_room", HueOptions { color: false, ..HueOptions::default() });
    b.switch(describe("lamp_hipster_room", "Studio Hipster Lamp", "💡", &["default"], None, "Studio"), device);

    let device = b.window(5, 6);
    b.switch(describe("window_kitchen", "Kitchen Window", "☀️", &[], None, "Windows"), device);

    let device = b.window(9, 13);
    b.switch(describe("window_living_room", "Living Room Window", "☀️", &[], None, "Windows"), device);

    let device = b.window(11, 27);
    b.switch(describe("window_tv", "TV Window", "☀️", &[], None, "Windows"), device);

    b.scene("random", "Random", "❓", Colors::Random, Effects::Same("Color Burst".into()), None, &[]);
    b.scene("hloop", "Random Loop", "🤓", Colors::Perturb { base: None, factor: 0.04 }, Effects::None, Some((5.0, 10.0)), &[]);
    b.scene(
        "natural",
        "Naturale",
        "🌞",
        Colors::Fixed(Hsb { hue: Some(0.13), saturation: Some(0.6), brightness: None }),
        per_panel("Flames", "Sundown"),
        None,
        &["default"],
    );
    b.scene("disco", "Disco", "🌐", Colors::Random, per_panel("Fireworks", "Beatdrop"), Some((0.3, 1.2)), &["default", "nanoleaf"]);

    for (icon, name, exa, colors) in [
        ("🌲", "Forest", "Jungle", around(0.297, 0.6, 0.15)),
        ("🎉", "Inner Peace", "Cotton Candy", Colors::Random),
        ("🎉", "Meteor Shower", "Waterfall", Colors::Random),
        ("🐟", "Nemo", "Sundown", around(0.080, 0.90, 0.04)),
        ("🎉", "Northern Lights", "Northern Lights", Colors::Random),
        ("🎉", "Paint Splatter", "Prism", Colors::Random),
        ("🎉", "Pulse Pop Beats", "Beatdrop", Colors::Random),
        ("🎉", "Rhythmic Northern Lights", "Hip Hop", Colors::Random),
        ("🎉", "Ripple", "Cocoa Beach", Colors::Random),
        ("❤️", "Romantic", "Date Night", around(0.8446, 1.0, 0.15)),
        ("⛄", "Snowfall", "Morning Sky", around(0.5952, 0.50, 0.04)),
        ("🎉", "Sound Bar", "Pop Rocks", Colors::Random),
        ("🎉", "Streaking Notes", "Lightscape", Colors::Random),
    ] {
        // the scene is named after the effect of the tv panel
        let id = format!("nanoleaf_{}", name.to_lowercase().replace(' ', "_"));
        b.scene(&id, name, icon, colors, per_panel(name, exa), None, &["nanoleaf"]);
    }

    let home = b.home.build();

    for scene in b.scenes {
        scene.attach(&home);
    }

    (home, simulated)
}
