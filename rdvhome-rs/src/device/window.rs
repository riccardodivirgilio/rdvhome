// A motorised shutter: one relay gives power to the motor, one picks the
// direction (both active low). The motor has no end switch we can read, so it
// is stopped after the time a full run takes.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use async_trait::async_trait;
use tokio::sync::broadcast;

use super::{changes, Capabilities, Changes, Command, Device, Direction, Report};
use crate::gpio::Gpio;

pub struct Window {
    gpio: Arc<dyn Gpio>,
    power: u8,
    direction: u8,
    changes: Changes,
    started: AtomicBool,
}

impl Window {
    pub fn new(gpio: Arc<dyn Gpio>, power: u8, direction: u8) -> Arc<Window> {
        gpio.setup_output(power);
        gpio.setup_output(direction);

        Arc::new(Window { gpio, power, direction, changes: changes(), started: AtomicBool::new(false) })
    }

    // (up, down)
    fn moving(&self) -> (bool, bool) {
        let powered = !self.gpio.read(self.power);
        let up = self.gpio.read(self.direction);

        (powered && up, powered && !up)
    }

    fn stop(&self) {
        self.gpio.write(self.power, true);
        self.gpio.write(self.direction, true);
    }

    fn report(&self) -> Report {
        Report { moving: Some(self.moving()), ..Report::full() }
    }

    // seconds for a full run
    fn timing(&self, direction: Direction) -> u32 {
        match (self.gpio.is_simulated(), direction) {
            (true, _) => 4,
            (false, Direction::Up) => 13,
            (false, Direction::Down) => 12,
        }
    }
}

#[async_trait]
impl Device for Window {
    fn capabilities(&self) -> Capabilities {
        Capabilities { direction: true, ..Capabilities::NONE }
    }

    async fn read(&self) -> Report {
        self.report()
    }

    // anything that is not "up" or "down" stops the motor
    async fn apply(&self, cmd: &Command) -> Report {
        match cmd.direction {
            None => self.stop(),
            Some(direction) => {
                let (up, down) = self.moving();

                if !(if direction == Direction::Up { up } else { down }) {
                    self.gpio.write(self.direction, direction == Direction::Up);
                    self.gpio.write(self.power, false);
                }
            }
        }

        self.report()
    }

    fn changes(&self) -> Option<broadcast::Receiver<()>> {
        Some(self.changes.subscribe())
    }

    fn start(self: Arc<Self>) {
        if self.started.swap(true, Ordering::SeqCst) {
            return;
        }

        // whatever was going on before the restart, the motor is off now
        self.stop();

        tokio::spawn(async move {
            let (mut up, mut down) = (0, 0);

            loop {
                tokio::time::sleep(Duration::from_secs(1)).await;

                let moving = self.moving();
                up = if moving.0 { up + 1 } else { 0 };
                down = if moving.1 { down + 1 } else { 0 };

                if up >= self.timing(Direction::Up) || down >= self.timing(Direction::Down) {
                    self.stop();
                    (up, down) = (0, 0);
                    let _ = self.changes.send(());
                }
            }
        });
    }
}
