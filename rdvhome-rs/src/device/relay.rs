// The physical switch: a relay in parallel with the wall button. A short low
// pulse toggles the mains, and a status pin senses if the mains is there
// (low = powered), so the truth is always read, never remembered.
//
// One Relay can power several lights (the two strips behind the tv): share it
// with Arc, the pulse is serialised so two commands do not toggle it twice.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use async_trait::async_trait;
use tokio::sync::{broadcast, Mutex};
use tokio::time::sleep;

use super::{changes, Capabilities, Changes, Command, Device, Report};
use crate::gpio::Gpio;

// How long the relay is held low.
//
// The python app asks for 25 ms, and porting that number verbatim was the one thing
// that did not survive the move: python asks a busy event loop that also blocks on
// prints, so what reached the board was much longer than 25 ms, while tokio sleeps
// for exactly what it is told. Measured on the house (2026-09-18, pin 23):
//
//   25 ms  -> the relay board pulls in but the impulse relay never latches, nothing happens
//   40 ms  -> latches, the status pin follows immediately
//   60 ms  -> latches
//
// So the real requirement was always above 25 ms and python only ever met it by being
// slow. 100 ms leaves a wide margin and is still well under the time a human holds a
// wall button. RDV_PULSE_MS overrides it without a rebuild.
fn pulse() -> Duration {
    static MS: std::sync::OnceLock<u64> = std::sync::OnceLock::new();

    Duration::from_millis(*MS.get_or_init(|| {
        std::env::var("RDV_PULSE_MS").ok().and_then(|v| v.parse().ok()).unwrap_or(100)
    }))
}

const WATCH: Duration = Duration::from_millis(300);
// how often the status pin is re-read after a pulse, for at most 20 tries
const SETTLE: Duration = Duration::from_millis(25);

fn label(on: bool) -> &'static str {
    if on {
        "on"
    } else {
        "off"
    }
}

pub struct Relay {
    id: String,
    gpio: Arc<dyn Gpio>,
    relay: u8,
    status: u8,
    pulsing: Mutex<()>,
    changes: Changes,
    started: AtomicBool,
}

impl Relay {
    pub fn new(id: &str, gpio: Arc<dyn Gpio>, relay: u8, status: u8) -> Arc<Relay> {
        println!("[BOOT] relay {} relay_pin={} status_pin={}", id, relay, status);

        gpio.setup_output(relay);
        gpio.setup_input(status);
        gpio.link(relay, status);

        Arc::new(Relay {
            id: id.to_string(),
            gpio,
            relay,
            status,
            pulsing: Mutex::new(()),
            changes: changes(),
            started: AtomicBool::new(false),
        })
    }

    pub fn is_powered(&self) -> bool {
        !self.gpio.read(self.status)
    }

    pub async fn set(&self, on: bool) {
        let _guard = self.pulsing.lock().await;
        let sensed = self.is_powered();

        if sensed == on {
            println!("[RELAY {}] asked {}, mains already {}, no pulse", self.id, label(on), label(sensed));
            return;
        }

        println!("[RELAY {}] asked {}, mains {}, pulsing pin {} low for {:?}", self.id, label(on), label(sensed), self.relay, pulse());

        let started = std::time::Instant::now();

        self.gpio.write(self.relay, false);
        sleep(pulse()).await;
        self.gpio.write(self.relay, true);

        let pulsed = started.elapsed();

        // the status pin follows the mains with some delay: wait for it, so
        // whoever is queued on the lock does not pulse again
        for _ in 0..20 {
            if self.is_powered() == on {
                break;
            }
            sleep(SETTLE).await;
        }

        // Python never waited here, so a relay that does not answer went unnoticed.
        // If this says "never followed", the pulse did not reach the mains.
        println!(
            "[RELAY {}] pulse held {:?}, status pin {} {} after {:?}",
            self.id,
            pulsed,
            self.status,
            if self.is_powered() == on { "followed" } else { "NEVER FOLLOWED" },
            started.elapsed()
        );
    }
}

#[async_trait]
impl Device for Relay {
    fn capabilities(&self) -> Capabilities {
        Capabilities::ON
    }

    async fn read(&self) -> Report {
        Report { on: Some(self.is_powered()), ..Report::full() }
    }

    async fn apply(&self, cmd: &Command) -> Report {
        if let Some(on) = cmd.on {
            self.set(on).await;
        }

        Report::echo(cmd)
    }

    async fn is_on(&self) -> bool {
        self.is_powered()
    }

    fn changes(&self) -> Option<broadcast::Receiver<()>> {
        Some(self.changes.subscribe())
    }

    fn start(self: Arc<Self>) {
        if self.started.swap(true, Ordering::SeqCst) {
            return;
        }

        tokio::spawn(async move {
            let mut powered = self.is_powered();

            loop {
                sleep(WATCH).await;

                if self.is_powered() != powered {
                    powered = !powered;
                    let _ = self.changes.send(());
                }
            }
        });
    }
}
