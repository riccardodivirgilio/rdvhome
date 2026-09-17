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

// What a request can say, as it arrives: everything is optional. The query
// string fills it first, what is in the path goes on top.
#[derive(Default)]
struct Params {
    // id or alias, nothing is "everything"
    number: Option<String>,
    // on, off, up, down, stop, or "-" for "leave it"
    mode: Option<String>,
    // a colour name or #hex...
    color: Option<String>,
    // ...or 0..100 each, "-" for "leave it"
    hue: Option<String>,
    saturation: Option<String>,
    brightness: Option<String>,
    effect: Option<String>,
}

impl Params {
    fn from_query(query: &str) -> Params {
        let mut params = Params::default();

        for pair in query.split('&').filter(|p| !p.is_empty()) {
            let (key, value) = pair.split_once('=').unwrap_or((pair, ""));

            let field = match percent_decode(key, true).as_str() {
                "number" => &mut params.number,
                "mode" => &mut params.mode,
                "color" => &mut params.color,
                "hue" => &mut params.hue,
                "saturation" => &mut params.saturation,
                "brightness" => &mut params.brightness,
                "effect" => &mut params.effect,
                _ => continue,
            };

            // the first one wins
            field.get_or_insert_with(|| percent_decode(value, true));
        }

        params
    }

    // Checked in the order of the old app (colour, components, mode): it decides which error comes out.
    fn command(&self) -> Result<Command, Failure> {
        // python truthiness: an empty argument is a missing one
        fn filled(field: &Option<String>) -> Option<&str> {
            field.as_deref().filter(|v| !v.is_empty())
        }

        let mut cmd = Command { effect: filled(&self.effect).map(|e| Effect::Named(e.to_string())), ..Command::default() };

        if let Some(color) = filled(&self.color) {
            cmd.color = Some(Hsb::parse(color).map_err(|e| match e {
                ColorError::Invalid => Failure::BadRequest("InvalidColor"),
                ColorError::Crash => Failure::Crash,
            })?);
        }

        let components = Hsb {
            hue: component(self.hue.as_deref())?,
            saturation: component(self.saturation.as_deref())?,
            brightness: component(self.brightness.as_deref())?,
        };

        // wins over a colour name
        if !components.is_empty() {
            cmd.color = Some(components);
        }

        match self.mode.as_deref() {
            Some("on") => cmd.on = Some(true),
            Some("off") => cmd.on = Some(false),
            Some("up") => cmd.direction = Some(Direction::Up),
            Some("down") => cmd.direction = Some(Direction::Down),
            Some("stop") | Some("-") | None => {}
            Some(_) => return Err(Failure::BadRequest("InvalidMode")),
        }

        Ok(cmd)
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

enum Route {
    Static(String),
    Homekit,
    Qrcode,
    // the state of the switches behind an alias, None is all of them
    Read { alias: Option<String> },
    Write { alias: Option<String>, command: Command },
}

impl Route {
    // also a read refuses bad parameters, like the old app
    fn read(params: Params) -> Result<Route, Failure> {
        params.command()?;
        Ok(Route::Read { alias: params.number.filter(|n| !n.is_empty()) })
    }

    fn write(params: Params) -> Result<Route, Failure> {
        Ok(Route::Write { command: params.command()?, alias: params.number.filter(|n| !n.is_empty()) })
    }
}

// Every url is a route with what it says in it; what the url does not say comes
// from the query string. Err(NotFound) is "no such url", the other errors are a
// bad request to a good url.
fn resolve(path: &str, query: &str) -> Result<Route, Failure> {
    let segments: Vec<&str> = path.strip_prefix('/').unwrap_or(path).split('/').collect();
    let query = Params::from_query(query);
    let some = |segment: &str| Some(segment.to_string());

    match segments[..] {
        [""] => Ok(Route::Static("index.html".to_string())),
        ["css" | "js", ..] => Ok(Route::Static(path[1..].to_string())),
        ["homekit"] => Ok(Route::Homekit),
        ["qrcode"] => Ok(Route::Qrcode),

        ["switch"] => Route::read(query),
        ["switch", number, ..] if !is_number(number) => Err(Failure::NotFound),
        ["switch", number] => Route::read(Params { number: some(number), ..query }),
        ["switch", number, "set"] => Route::write(Params { number: some(number), ..query }),
        ["switch", number, "color", color] if is_color(color) => {
            Route::write(Params { number: some(number), color: some(color), ..query })
        }
        ["switch", number, mode] if is_mode(mode) => Route::write(Params { number: some(number), mode: some(mode), ..query }),
        ["switch", number, mode, hue, saturation, brightness]
            if is_mode(mode) && is_component(hue) && is_component(saturation) && is_component(brightness) =>
        {
            Route::write(Params {
                number: some(number),
                mode: some(mode),
                hue: some(hue),
                saturation: some(saturation),
                brightness: some(brightness),
                ..query
            })
        }

        _ => Err(Failure::NotFound),
    }
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
    let route = resolve(&percent_decode(path, false), query);

    // the old app answers 500 to anything that is not a GET on a url it knows (its 405 was handled as a crash)
    let route = match route {
        Err(Failure::NotFound) => return failure(Failure::NotFound),
        _ if !matches!(method, "GET" | "WS") => return failure(Failure::Crash),
        Err(e) => return failure(e),
        Ok(route) => route,
    };

    match route {
        // like aiohttp: a folder is forbidden, a missing file is an empty 404
        Route::Static(name) => match FRONTEND.get_file(&name) {
            Some(file) => Answer { status: 200, content_type: content_type(&name), body: file.contents().to_vec() },
            None if FRONTEND.get_dir(name.trim_end_matches('/')).is_some() => failure(Failure::Forbidden),
            None => Answer { status: 404, content_type: "application/octet-stream", body: Vec::new() },
        },
        Route::Homekit => match homekit::pairing(None) {
            Some(pairing) => envelope(
                200,
                Map::from_iter([("paircode".to_string(), json!(pairing.paircode)), ("uri".to_string(), json!(pairing.uri))]),
            ),
            None => failure(Failure::Crash),
        },
        Route::Qrcode => match homekit::pairing(None) {
            Some(pairing) => Answer { status: 200, content_type: "image/svg+xml", body: pairing.qrcode_svg().into_bytes() },
            None => failure(Failure::Crash),
        },
        Route::Read { alias } => switches(Home::status(&home.filter(alias.as_deref())).await),
        Route::Write { alias, command } => switches(Home::apply(&home.filter(alias.as_deref()), &command).await),
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
