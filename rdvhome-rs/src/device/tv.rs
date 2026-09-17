// Samsung tv: "is it on" is "does its api answer", asked every 15 seconds.
// It can only be switched off (KEY_POWER over its websocket).

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use async_trait::async_trait;
use futures_util::{SinkExt, StreamExt};
use tokio::sync::broadcast;
use tokio_tungstenite::tungstenite::Message;

use super::{changes, Capabilities, Changes, Command, Device, Report};

const POLL: Duration = Duration::from_secs(15);
const TIMEOUT: Duration = Duration::from_secs(1);

pub struct Tv {
    host: String,
    client: reqwest::Client,
    on: AtomicBool,
    changes: Changes,
    started: AtomicBool,
}

impl Tv {
    pub fn new(host: &str) -> Arc<Tv> {
        Arc::new(Tv {
            host: host.to_string(),
            client: reqwest::Client::builder().timeout(TIMEOUT).connect_timeout(TIMEOUT).build().expect("client"),
            on: AtomicBool::new(false),
            changes: changes(),
            started: AtomicBool::new(false),
        })
    }

    async fn answers(&self) -> bool {
        self.client.get(format!("http://{}:8001/api/v2/", self.host)).send().await.is_ok()
    }

    async fn press(&self, key: &str) -> Result<(), tokio_tungstenite::tungstenite::Error> {
        let url = format!("ws://{}:8001/api/v2/channels/samsung.remote.control", self.host);
        let (mut socket, _) = tokio_tungstenite::connect_async(url).await?;

        while let Some(message) = socket.next().await {
            if message?.to_text().is_ok_and(|text| text.contains("ms.channel.connect")) {
                let click = format!(
                    r#"{{"method":"ms.remote.control","params":{{"Cmd":"Click","DataOfCmd":"{}","Option":"false","TypeOfRemote":"SendRemoteKey"}}}}"#,
                    key
                );
                socket.send(Message::text(click)).await?;
                break;
            }
        }

        socket.close(None).await
    }

    fn report(&self) -> Report {
        let on = self.on.load(Ordering::SeqCst);
        Report { on: Some(on), allow_on: Some(on), ..Report::full() }
    }
}

#[async_trait]
impl Device for Tv {
    fn capabilities(&self) -> Capabilities {
        Capabilities::NONE
    }

    async fn read(&self) -> Report {
        self.report()
    }

    async fn apply(&self, cmd: &Command) -> Report {
        if let Some(on) = cmd.on {
            if on != self.on.load(Ordering::SeqCst) {
                if !on && self.answers().await {
                    if let Err(e) = tokio::time::timeout(TIMEOUT * 5, self.press("KEY_POWER")).await {
                        eprintln!("tv: {}", e);
                    }
                }
                self.on.store(on, Ordering::SeqCst);
            }
        }

        self.report()
    }

    async fn is_on(&self) -> bool {
        self.on.load(Ordering::SeqCst)
    }

    fn changes(&self) -> Option<broadcast::Receiver<()>> {
        Some(self.changes.subscribe())
    }

    fn start(self: Arc<Self>) {
        if self.started.swap(true, Ordering::SeqCst) {
            return;
        }

        tokio::spawn(async move {
            loop {
                let on = self.answers().await;

                if on != self.on.swap(on, Ordering::SeqCst) {
                    let _ = self.changes.send(());
                }

                tokio::time::sleep(POLL).await;
            }
        });
    }
}
