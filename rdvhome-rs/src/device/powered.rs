// A light behind a physical switch: Powered(relay, hue strip).
// This is the only place that knows how the two combine:
//
//   on        power OR light    whoever can see it is on, is right
//   allow_on  power OR light    no mains makes the bulb unreachable, but the
//                               relay can always bring it back
//   commands  to both, in sync  power first, so the bulb is there to listen
//   changes   from either
//
// `on` used to be an AND, copied from the python `is_on`. On the house that reads
// wrong: two strips share one relay (led_tv, led_living_room), so switching one
// powers both, but the other only learned it was on when the hue poll came back —
// it showed off for seconds, or for as long as the bridge was offline, while it was
// visibly lit in the room. The wiring knows the mains is there straight away, so one
// device reporting on is enough; it takes all of them saying off to be off.
//
// The trade-off, on purpose: a strip left powered but switched off from the Hue app
// reads as on here. Mains is the switch people actually use in this house.
//
// Colours and effects belong to the light alone.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use async_trait::async_trait;
use tokio::sync::broadcast;

use super::{changed, changes, Capabilities, Changes, Command, Device, Report};

pub struct Powered<P: Device, L: Device> {
    power: Arc<P>,
    light: Arc<L>,
    changes: Changes,
    started: AtomicBool,
}

impl<P: Device, L: Device> Powered<P, L> {
    pub fn new(power: Arc<P>, light: Arc<L>) -> Arc<Self> {
        Arc::new(Powered { power, light, changes: changes(), started: AtomicBool::new(false) })
    }
}

#[async_trait]
impl<P: Device, L: Device> Device for Powered<P, L> {
    fn capabilities(&self) -> Capabilities {
        let (power, light) = (self.power.capabilities(), self.light.capabilities());

        Capabilities { on: power.on || light.on, ..light }
    }

    fn effects(&self) -> &[String] {
        self.light.effects()
    }

    async fn read(&self) -> Report {
        let (power, light) = tokio::join!(self.power.read(), self.light.read());

        Report {
            on: Some(power.on.unwrap_or(false) || light.on.unwrap_or(false)),
            allow_on: Some(
                power.allow_on.unwrap_or(self.power.capabilities().on)
                    || light.allow_on.unwrap_or(self.light.capabilities().on),
            ),
            ..light
        }
    }

    async fn apply(&self, cmd: &Command) -> Report {
        if let Some(on) = cmd.on {
            self.power.apply(&Command::on(on)).await;
        }

        // the light always hears the whole command, also "off": when the mains
        // comes back from the wall switch it must not shine on its own
        self.light.apply(cmd).await
    }

    async fn is_on(&self) -> bool {
        self.power.is_on().await || self.light.is_on().await
    }

    fn changes(&self) -> Option<broadcast::Receiver<()>> {
        Some(self.changes.subscribe())
    }

    fn start(self: Arc<Self>) {
        if self.started.swap(true, Ordering::SeqCst) {
            return;
        }

        for source in [self.power.changes(), self.light.changes()].into_iter().flatten() {
            let (mut source, changes) = (source, self.changes.clone());

            tokio::spawn(async move {
                while changed(&mut source).await {
                    let _ = changes.send(());
                }
            });
        }

        self.power.clone().start();
        self.light.clone().start();
    }
}
