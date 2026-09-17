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

const PULSE: Duration = Duration::from_millis(25);
const WATCH: Duration = Duration::from_millis(300);

pub struct Relay {
    gpio: Arc<dyn Gpio>,
    relay: u8,
    status: u8,
    pulsing: Mutex<()>,
    changes: Changes,
    started: AtomicBool,
}

impl Relay {
    pub fn new(gpio: Arc<dyn Gpio>, relay: u8, status: u8) -> Arc<Relay> {
        gpio.setup_output(relay);
        gpio.setup_input(status);
        gpio.link(relay, status);

        Arc::new(Relay { gpio, relay, status, pulsing: Mutex::new(()), changes: changes(), started: AtomicBool::new(false) })
    }

    pub fn is_powered(&self) -> bool {
        !self.gpio.read(self.status)
    }

    pub async fn set(&self, on: bool) {
        let _guard = self.pulsing.lock().await;

        if self.is_powered() == on {
            return;
        }

        self.gpio.write(self.relay, false);
        sleep(PULSE).await;
        self.gpio.write(self.relay, true);

        // the status pin follows the mains with some delay: wait for it, so
        // whoever is queued on the lock does not pulse again
        for _ in 0..20 {
            if self.is_powered() == on {
                break;
            }
            sleep(PULSE).await;
        }
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
