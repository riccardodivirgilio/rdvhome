// rdvhome: the lights, windows and scenes of the house behind one http api.
// Rust port of the python app in ../rdvhome, see ../knowledge/RDVHOME-RS.md.

mod color;
mod color_names;
mod device;
mod gpio;
mod hap;
mod home;
mod homekit;
mod json;
mod server;
mod store;
mod switch;

use std::time::Duration;

use device::Command;
use switch::Home;

const COMMANDS: [&str; 5] = ["off", "on", "pair", "run", "test_gpio"];

fn usage() {
    println!("Select one of the following commands:");
    for command in COMMANDS {
        println!(" - {}", command);
    }
}

fn help(name: &str, description: &str, arguments: &str) -> bool {
    let wanted = std::env::args().skip(2).any(|a| a == "-h" || a == "--help");

    if wanted {
        println!("usage: rdvhome {} [-h]{}\n\n{}", name, arguments, description);
    }

    wanted
}

// on / off: straight to the devices, no server needed
async fn switch(on: bool, default: &str) {
    let mut aliases: Vec<String> = std::env::args().skip(2).collect();

    if aliases.is_empty() {
        aliases.push(default.to_string());
    }

    let (home, _) = home::build();
    let mut ids: Vec<String> = Home::apply(&home.filter_any(&aliases), &Command::on(on)).await.keys().cloned().collect();
    ids.sort();

    println!("{}", [vec![if on { "on:" } else { "off:" }.to_string()], ids].concat().join(" "));
}

async fn test_gpio() {
    let gpio = gpio::open();

    for pin in home::RELAY2 {
        gpio.setup_output(pin);
    }

    for (label, high) in [("on", false), ("off", true)] {
        for pin in home::RELAY2 {
            println!("RELAY {:02} {}", pin, label);
            gpio.write(pin, high);
            tokio::time::sleep(Duration::from_millis(200)).await;
        }

        if !high {
            tokio::time::sleep(Duration::from_secs(1)).await;
        }
    }
}

#[tokio::main]
async fn main() {
    let command = std::env::args().nth(1).unwrap_or_default();

    match command.as_str() {
        "run" => {
            if help("run", "Run the home app", " [--open]") {
                return;
            }

            let (home, simulated) = home::build();
            home.start();
            tokio::spawn(homekit::serve(home.clone(), store::data_dir(simulated), simulated));

            let stop = async {
                let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()).expect("signal");
                tokio::select! {
                    _ = term.recv() => {}
                    _ = tokio::signal::ctrl_c() => {}
                }
            };

            tokio::select! {
                result = server::serve(home, "0.0.0.0", 8500) => {
                    if let Err(e) = result {
                        eprintln!("server: {}", e);
                        std::process::exit(1);
                    }
                }
                _ = stop => {}
            }
        }
        "on" if !help("on", "Switch on the lights", " [args ...]") => switch(true, "default").await,
        "off" if !help("off", "Switch off the lights", " [args ...]") => switch(false, "all").await,
        "on" | "off" => {}
        "pair" => {
            let simulated = gpio::open().is_simulated();

            if let Some(pairing) = homekit::pairing(Some(store::data_dir(simulated))) {
                println!("Setup payload: {}", pairing.uri);
                println!("Scan this code with your HomeKit app on your iOS device:\n\n{}\n", pairing.qrcode_text());
                println!("Or enter this code in your HomeKit app on your iOS device: {}", pairing.paircode);
            }
        }
        "test_gpio" => test_gpio().await,
        _ => usage(),
    }
}
