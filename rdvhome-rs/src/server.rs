// The http api and the websocket, same urls and same bytes as the aiohttp app.
//
// Routing is one function, `route`, used by both: the websocket clients send
// the path of the request as text ("/switch/led_tv/on") and get no answer,
// what happened comes back to everybody as events.

use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use axum::body::Body;
use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::State;
use axum::http::{header, Method, Request, StatusCode};
use axum::response::Response;
use axum::routing::any;
use axum::Router;
use futures_util::{SinkExt, StreamExt};
use include_dir::{include_dir, Dir};
use serde_json::{json, Map, Value};
use tokio::sync::broadcast::error::RecvError;

use crate::color::{ColorError, Hsb};
use crate::device::{Command, Direction, Effect};
use crate::homekit;
use crate::json::dumps;
use crate::switch::Home;

static FRONTEND: Dir = include_dir!("$CARGO_MANIFEST_DIR/../rdvhome/frontend/dist");

pub struct Answer {
    pub status: u16,
    pub content_type: &'static str,
    pub body: Vec<u8>,
}

enum Failure {
    BadRequest(&'static str),
    Forbidden,
    NotFound,
    // where the old app raises an exception
    Crash,
}

fn envelope(status: u16, mut fields: Map<String, Value>) -> Answer {
    let unixtime = SystemTime::now().duration_since(UNIX_EPOCH).map_or(0.0, |d| d.as_micros() as f64 / 1e6);

    fields.insert("status".into(), json!(status));
    fields.insert("success".into(), json!(status == 200));
    fields.insert("unixtime".into(), json!(unixtime));

    Answer { status, content_type: "text/plain; charset=utf-8", body: dumps(&fields).into_bytes() }
}

fn failure(failure: Failure) -> Answer {
    let (status, reason) = match failure {
        Failure::BadRequest(reason) => (400, Some(reason)),
        Failure::Forbidden => (403, Some("Forbidden")),
        Failure::NotFound => (404, Some("Not Found")),
        Failure::Crash => (500, None),
    };

    envelope(status, reason.map(|r| ("reason".to_string(), json!(r))).into_iter().collect())
}

fn switches(switches: Map<String, Value>) -> Answer {
    let status = if switches.is_empty() { 404 } else { 200 };

    envelope(status, Map::from_iter([("mode".to_string(), json!("status")), ("switches".to_string(), Value::Object(switches))]))
}

fn percent_decode(text: &str, plus: bool) -> String {
    let bytes = text.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut i = 0;

    while i < bytes.len() {
        let hex = |b: u8| (b as char).to_digit(16);

        match bytes[i] {
            b'%' if i + 2 < bytes.len() => match (hex(bytes[i + 1]), hex(bytes[i + 2])) {
                (Some(high), Some(low)) => {
                    out.push((high * 16 + low) as u8);
                    i += 2;
                }
                _ => out.push(b'%'),
            },
            b'+' if plus => out.push(b' '),
            byte => out.push(byte),
        }
        i += 1;
    }

    String::from_utf8_lossy(&out).into_owned()
}

// the arguments of a request: the query string, then the path on top of it
#[derive(Default)]
struct Args {
    values: Vec<(String, String)>,
}

impl Args {
    fn from_query(query: &str) -> Args {
        let mut args = Args::default();

        for pair in query.split('&').filter(|p| !p.is_empty()) {
            let (key, value) = pair.split_once('=').unwrap_or((pair, ""));
            let key = percent_decode(key, true);

            // the first one wins
            if args.get(&key).is_none() {
                args.values.push((key, percent_decode(value, true)));
            }
        }

        args
    }

    fn set(&mut self, key: &str, value: &str) {
        self.values.retain(|(k, _)| k != key);
        self.values.push((key.to_string(), value.to_string()));
    }

    fn get(&self, key: &str) -> Option<&str> {
        self.values.iter().find(|(k, _)| k == key).map(|(_, v)| v.as_str())
    }

    // python truthiness: a missing and an empty argument are the same
    fn filled(&self, key: &str) -> Option<&str> {
        self.get(key).filter(|v| !v.is_empty())
    }
}

// int() of python: spaces around, a sign, digits with single underscores
fn python_int(text: &str) -> Option<i128> {
    let text = text.trim();
    let digits = text.strip_prefix(['+', '-']).unwrap_or(text);

    let well_formed = !digits.is_empty()
        && digits.split('_').all(|group| !group.is_empty() && group.bytes().all(|b| b.is_ascii_digit()));

    if !well_formed {
        return None;
    }

    // too big to be in range anyway
    let value = digits.replace('_', "").parse::<i128>().unwrap_or(i128::MAX);
    Some(if text.starts_with('-') { -value } else { value })
}

// "-" or 0..100
fn component(spec: Option<&str>) -> Result<Option<f64>, Failure> {
    match spec {
        None | Some("-") => Ok(None),
        Some(spec) => match python_int(spec) {
            None => Err(Failure::BadRequest("NotAnInteger")),
            Some(value) if !(0..=100).contains(&value) => Err(Failure::BadRequest("NotInRange")),
            Some(value) => Ok(Some(value as f64 / 100.0)),
        },
    }
}

fn command(args: &Args) -> Result<Command, Failure> {
    let mut cmd = Command { effect: args.filled("effect").map(|e| Effect::Named(e.to_string())), ..Command::default() };

    if let Some(color) = args.filled("color") {
        cmd.color = Some(Hsb::parse(color).map_err(|e| match e {
            ColorError::Invalid => Failure::BadRequest("InvalidColor"),
            ColorError::Crash => Failure::Crash,
        })?);
    }

    let components = Hsb {
        hue: component(args.get("hue"))?,
        saturation: component(args.get("saturation"))?,
        brightness: component(args.get("brightness"))?,
    };

    // wins over a colour name
    if !components.is_empty() {
        cmd.color = Some(components);
    }

    match args.get("mode") {
        Some("on") => cmd.on = Some(true),
        Some("off") => cmd.on = Some(false),
        Some("up") => cmd.direction = Some(Direction::Up),
        Some("down") => cmd.direction = Some(Direction::Down),
        Some("stop") | Some("-") | None => {}
        Some(_) => return Err(Failure::BadRequest("InvalidMode")),
    }

    Ok(cmd)
}

fn is_number(segment: &str) -> bool {
    !segment.is_empty() && segment.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}

fn is_color(segment: &str) -> bool {
    !segment.is_empty() && segment.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
}

fn is_mode(segment: &str) -> bool {
    matches!(segment, "-" | "on" | "off" | "up" | "down" | "stop")
}

fn is_component(segment: &str) -> bool {
    segment == "-" || (!segment.is_empty() && segment.bytes().all(|b| b.is_ascii_digit()))
}

enum Route<'a> {
    Static(&'a str),
    Homekit,
    Qrcode,
    Status,
    Switch,
}

fn resolve<'a>(path: &'a str, segments: &[&'a str], args: &mut Args) -> Option<Route<'a>> {
    let route = match segments {
        [""] => Route::Static("index.html"),
        ["css" | "js", ..] => Route::Static(&path[1..]),
        ["homekit"] => Route::Homekit,
        ["qrcode"] => Route::Qrcode,
        ["switch"] => Route::Status,
        ["switch", number, rest @ ..] if is_number(number) => {
            let route = match rest {
                [] => Route::Status,
                ["set"] => Route::Switch,
                ["color", color] if is_color(color) => {
                    args.set("color", color);
                    Route::Switch
                }
                [mode] if is_mode(mode) => {
                    args.set("mode", mode);
                    Route::Switch
                }
                [mode, hue, saturation, brightness] if is_mode(mode) && [hue, saturation, brightness].iter().all(|c| is_component(c)) => {
                    args.set("mode", mode);
                    args.set("hue", hue);
                    args.set("saturation", saturation);
                    args.set("brightness", brightness);
                    Route::Switch
                }
                _ => return None,
            };
            args.set("number", number);
            route
        }
        _ => return None,
    };

    Some(route)
}

fn content_type(path: &str) -> &'static str {
    match path.rsplit('.').next() {
        Some("html") => "text/html",
        Some("css") => "text/css",
        Some("js") => "text/javascript",
        Some("map") | Some("json") => "application/json",
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        Some("ico") => "image/x-icon",
        _ => "application/octet-stream",
    }
}

// method is GET, or WS for what comes from a websocket
pub async fn route(home: &Home, method: &str, target: &str) -> Answer {
    let (path, query) = target.split_once('?').unwrap_or((target, ""));
    let path = percent_decode(path, false);
    let segments: Vec<&str> = path.strip_prefix('/').unwrap_or(&path).split('/').collect();
    let mut args = Args::from_query(query);

    let Some(route) = resolve(&path, &segments, &mut args) else { return failure(Failure::NotFound) };

    // the old app answers 500 to anything that is not a GET (its 405 was handled as a crash)
    if !matches!(method, "GET" | "WS") {
        return failure(Failure::Crash);
    }

    match route {
        // like aiohttp: a folder is forbidden, a missing file is an empty 404
        Route::Static(name) => match FRONTEND.get_file(name) {
            Some(file) => Answer { status: 200, content_type: content_type(name), body: file.contents().to_vec() },
            None if FRONTEND.get_dir(name.trim_end_matches('/')).is_some() => failure(Failure::Forbidden),
            None => Answer { status: 404, content_type: "application/octet-stream", body: Vec::new() },
        },
        Route::Homekit => match homekit::pairing() {
            Some(pairing) => envelope(
                200,
                Map::from_iter([("paircode".to_string(), json!(pairing.paircode)), ("uri".to_string(), json!(pairing.uri))]),
            ),
            None => failure(Failure::Crash),
        },
        Route::Qrcode => match homekit::pairing() {
            Some(pairing) => Answer { status: 200, content_type: "image/svg+xml", body: pairing.qrcode_svg().into_bytes() },
            None => failure(Failure::Crash),
        },
        Route::Status | Route::Switch => {
            let cmd = match command(&args) {
                Ok(cmd) => cmd,
                Err(e) => return failure(e),
            };
            let selected = home.filter(args.filled("number"));

            switches(match route {
                Route::Switch => Home::apply(&selected, &cmd).await,
                _ => Home::status(&selected).await,
            })
        }
    }
}

async fn http(State(home): State<Arc<Home>>, request: Request<Body>) -> Response {
    let target = request.uri().path_and_query().map_or("/", |t| t.as_str()).to_string();
    let answer = route(&home, request.method().as_str(), &target).await;

    Response::builder()
        .status(StatusCode::from_u16(answer.status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR))
        .header(header::CONTENT_TYPE, answer.content_type)
        .body(if request.method() == Method::HEAD { Body::empty() } else { Body::from(answer.body) })
        .expect("response")
}

async fn websocket(State(home): State<Arc<Home>>, upgrade: WebSocketUpgrade) -> Response {
    upgrade.on_upgrade(move |socket| serve_socket(home, socket))
}

async fn serve_socket(home: Arc<Home>, socket: WebSocket) {
    let (mut sender, mut receiver) = socket.split();
    let mut events = home.subscribe();

    let forward = tokio::spawn(async move {
        loop {
            match events.recv().await {
                Ok(event) => {
                    if sender.send(Message::text(event.text.as_str())).await.is_err() {
                        break;
                    }
                }
                Err(RecvError::Lagged(_)) => continue,
                Err(RecvError::Closed) => break,
            }
        }
    });

    while let Some(Ok(message)) = receiver.next().await {
        match message {
            Message::Text(text) if text.as_str() == "/close" => break,
            // no answer: what happens is in the events
            Message::Text(text) => drop(route(&home, "WS", text.as_str()).await),
            Message::Close(_) => break,
            _ => {}
        }
    }

    forward.abort();
}

pub async fn serve(home: Arc<Home>, address: &str, port: u16) -> std::io::Result<()> {
    let app = Router::new().route("/websocket", any(websocket)).fallback(http).with_state(home);
    let listener = tokio::net::TcpListener::bind((address, port)).await?;

    println!("======== Running on http://{}:{} ========", address, port);
    axum::serve(listener, app).await
}
