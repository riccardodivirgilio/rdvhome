// The raspberry pins. RealGpio on the raspberry, FileGpio everywhere else:
// one gpio-<pin>.json per pin (like the python DebugGPIO), so the app runs on
// a laptop or in docker and the pins can be inspected / edited by hand.

use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use crate::store::Store;

pub trait Gpio: Send + Sync {
    fn is_simulated(&self) -> bool;
    // input with pull-up
    fn setup_input(&self, pin: u8);
    // output, high at start (the relay boards are active low)
    fn setup_output(&self, pin: u8);
    fn read(&self, pin: u8) -> bool;
    fn write(&self, pin: u8, high: bool);
    // Tell a simulated board that pulsing `relay` toggles what `status` senses,
    // like the real wiring does. Nothing to do on the real one.
    fn link(&self, _relay: u8, _status: u8) {}
}

pub fn open() -> Arc<dyn Gpio> {
    #[cfg(all(target_os = "linux", any(target_arch = "arm", target_arch = "aarch64")))]
    if let Some(gpio) = real::RealGpio::new() {
        println!("[GPIO] using the raspberry pins");
        return Arc::new(gpio);
    }

    println!("[GPIO] raspberry pins not available, using files");
    Arc::new(FileGpio::new(crate::store::data_dir(true)))
}

pub struct FileGpio {
    store: Store,
    configured: Mutex<Vec<u8>>,
    links: Mutex<HashMap<u8, u8>>,
}

impl FileGpio {
    pub fn new(path: PathBuf) -> FileGpio {
        FileGpio { store: Store::new(path, "gpio"), configured: Mutex::default(), links: Mutex::default() }
    }

    fn first_time(&self, pin: u8) -> bool {
        let mut configured = self.configured.lock().unwrap();
        let new = !configured.contains(&pin);
        configured.push(pin);
        new
    }
}

impl Gpio for FileGpio {
    fn is_simulated(&self) -> bool {
        true
    }

    fn setup_input(&self, pin: u8) {
        if self.first_time(pin) && self.store.get::<u8>(&pin.to_string()).is_none() {
            self.store.set(&pin.to_string(), &1);
        }
    }

    fn setup_output(&self, pin: u8) {
        if self.first_time(pin) {
            self.store.set(&pin.to_string(), &1);
        }
    }

    fn read(&self, pin: u8) -> bool {
        self.store.get::<u8>(&pin.to_string()) == Some(1)
    }

    fn write(&self, pin: u8, high: bool) {
        self.store.set(&pin.to_string(), &(high as u8));

        if !high {
            if let Some(status) = self.links.lock().unwrap().get(&pin) {
                let sensed = self.read(*status);
                self.store.set(&status.to_string(), &(!sensed as u8));
            }
        }
    }

    fn link(&self, relay: u8, status: u8) {
        self.links.lock().unwrap().insert(relay, status);
    }
}

#[cfg(all(target_os = "linux", any(target_arch = "arm", target_arch = "aarch64")))]
mod real {
    use std::collections::HashMap;
    use std::sync::Mutex;

    use rppal::gpio::{Gpio as Board, InputPin, OutputPin};

    use super::Gpio;

    enum Pin {
        Input(InputPin),
        Output(OutputPin),
    }

    pub struct RealGpio {
        board: Board,
        pins: Mutex<HashMap<u8, Pin>>,
    }

    impl RealGpio {
        pub fn new() -> Option<RealGpio> {
            Some(RealGpio { board: Board::new().ok()?, pins: Mutex::default() })
        }
    }

    impl Gpio for RealGpio {
        fn is_simulated(&self) -> bool {
            false
        }

        fn setup_input(&self, pin: u8) {
            let mut pins = self.pins.lock().unwrap();

            if !pins.contains_key(&pin) {
                match self.board.get(pin) {
                    Ok(p) => drop(pins.insert(pin, Pin::Input(p.into_input_pullup()))),
                    Err(e) => eprintln!("[GPIO] setup_input pin={} ERROR: {}", pin, e),
                }
            }
        }

        fn setup_output(&self, pin: u8) {
            let mut pins = self.pins.lock().unwrap();

            if !pins.contains_key(&pin) {
                match self.board.get(pin) {
                    Ok(p) => {
                        let mut p = p.into_output_high();
                        // leave the relays as they are when the app stops
                        p.set_reset_on_drop(false);
                        pins.insert(pin, Pin::Output(p));
                    }
                    Err(e) => eprintln!("[GPIO] setup_output pin={} ERROR: {}", pin, e),
                }
            }
        }

        fn read(&self, pin: u8) -> bool {
            match self.pins.lock().unwrap().get(&pin) {
                Some(Pin::Input(p)) => p.is_high(),
                Some(Pin::Output(p)) => p.is_set_high(),
                None => true,
            }
        }

        fn write(&self, pin: u8, high: bool) {
            println!("[GPIO] output pin={} high={}", pin, high);

            if let Some(Pin::Output(p)) = self.pins.lock().unwrap().get_mut(&pin) {
                p.write(if high { rppal::gpio::Level::High } else { rppal::gpio::Level::Low });
            }
        }
    }
}
