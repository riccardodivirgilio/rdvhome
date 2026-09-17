// The command line, same commands as the python app (./run.sh <command>):
//
//   rdvhome run [--open]      the server (http :8500, homekit :51826)
//   rdvhome on [alias...]     straight to the devices, no server needed
//   rdvhome off [alias...]
//   rdvhome pair              the homekit setup code
//   rdvhome test_gpio         clicks the relays one by one

use std::time::Duration;

use clap::{CommandFactory, Parser, Subcommand};

use crate::device::Command;
use crate::switch::Home;
use crate::{gpio, home, homekit, server, store};

const ADDRESS: &str = "0.0.0.0";
const PORT: u16 = 8500;

#[derive(Parser)]
#[command(name = "rdvhome", about = "The lights, windows and scenes of the house behind one http api")]
struct Cli {
    #[command(subcommand)]
    command: Option<Action>,
}

#[derive(Subcommand)]
enum Action {
    /// Run the home app
    Run {
        /// Open the app in the browser
        #[arg(long)]
        open: bool,
    },
    /// Switch on the lights
    On {
        /// Ids or aliases
        #[arg(default_value = "default")]
        aliases: Vec<String>,
    },
    /// Switch off the lights
    Off {
        /// Ids or aliases
        #[arg(default_value = "all")]
        aliases: Vec<String>,
    },
    /// Pair homekit
    Pair,
    /// Test GPIO
    #[command(name = "test_gpio")]
    TestGpio,
}

pub async fn main() {
    match Cli::parse().command {
        Some(Action::Run { open }) => run(open).await,
        Some(Action::On { aliases }) => switch(true, &aliases).await,
        Some(Action::Off { aliases }) => switch(false, &aliases).await,
        Some(Action::Pair) => pair(),
        Some(Action::TestGpio) => test_gpio().await,
        // like the python app: no command lists them
        None => {
            println!("Select one of the following commands:");
            let mut names: Vec<String> = Cli::command().get_subcommands().map(|c| c.get_name().to_string()).collect();
            names.sort();

            for name in names {
                println!(" - {}", name);
            }
        }
    }
}

async fn run(open: bool) {
    let (home, simulated) = home::build();
    home.start();
    tokio::spawn(homekit::serve(home.clone(), store::data_dir(simulated), simulated));

    if open {
        let opener = if cfg!(target_os = "macos") { "open" } else { "xdg-open" };
        let _ = std::process::Command::new(opener).arg(format!("http://{}:{}", ADDRESS, PORT)).spawn();
    }

    let stop = async {
        let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()).expect("signal");
        tokio::select! {
            _ = term.recv() => {}
            _ = tokio::signal::ctrl_c() => {}
        }
    };

    tokio::select! {
        result = server::serve(home, ADDRESS, PORT) => {
            if let Err(e) = result {
                eprintln!("server: {}", e);
                std::process::exit(1);
            }
        }
        _ = stop => {}
    }
}

// prints "on: <ids>" like the python command
async fn switch(on: bool, aliases: &[String]) {
    let (home, _) = home::build();
    let mut ids: Vec<String> = Home::apply(&home.filter_any(aliases), &Command::on(on)).await.keys().cloned().collect();
    ids.sort();

    println!("{}", [vec![if on { "on:" } else { "off:" }.to_string()], ids].concat().join(" "));
}

fn pair() {
    let simulated = gpio::open().is_simulated();

    if let Some(pairing) = homekit::pairing(Some(store::data_dir(simulated))) {
        println!("Setup payload: {}", pairing.uri);
        println!("Scan this code with your HomeKit app on your iOS device:\n\n{}\n", pairing.qrcode_text());
        println!("Or enter this code in your HomeKit app on your iOS device: {}", pairing.paircode);
    }
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
