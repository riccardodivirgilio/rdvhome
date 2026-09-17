// Mock server built on the raw HTTP pairs captured by ../mock-capture.py.
//
// Every captures/*.http file is a request/response pair. The device state is
// seeded from the captured GETs and kept in memory (see device.rs): a PUT changes
// it and the next GET reads it back, until the server restarts. Responses reuse
// the captured status line and headers.
//
// Anything device.rs does not handle is answered with the response of the capture
// that has the same method and the most similar path. The access token is always
// ignored: everybody is authenticated.
//
// This file is identical in mock-philips and mock-nanoleaf, device.rs differs.

mod device;

use std::env;
use std::fs;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;

const SEPARATOR: &[u8] = b"\n\n======== RESPONSE ========\n\n";

pub struct Capture {
    pub name: String,
    pub method: String,
    pub path: String,
    pub body: Vec<u8>,
    pub response: Vec<u8>,
}

fn find(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack.windows(needle.len()).position(|w| w == needle)
}

fn request_line(raw: &[u8]) -> Option<(String, String)> {
    let line = String::from_utf8_lossy(&raw[..find(raw, b"\r\n")?]).to_string();
    let mut parts = line.split(' ');
    Some((parts.next()?.to_string(), parts.next()?.to_string()))
}

pub fn body(raw: &[u8]) -> &[u8] {
    find(raw, b"\r\n\r\n").map_or(&[], |position| &raw[position + 4..])
}

fn load_captures(dir: &str) -> Vec<Capture> {
    let mut paths: Vec<_> = fs::read_dir(dir)
        .unwrap_or_else(|e| panic!("cannot read {}: {}", dir, e))
        .map(|entry| entry.unwrap().path())
        .filter(|path| path.extension().map_or(false, |ext| ext == "http"))
        .collect();
    paths.sort();

    paths
        .iter()
        .map(|path| {
            let raw = fs::read(path).unwrap();
            let split = find(&raw, SEPARATOR).expect("missing response separator");
            let (method, path_) = request_line(&raw).expect("bad request line");
            Capture {
                name: path.file_name().unwrap().to_string_lossy().to_string(),
                method,
                path: path_,
                body: body(&raw[..split]).to_vec(),
                response: raw[split + SEPARATOR.len()..].to_vec(),
            }
        })
        .collect()
}

// same method, same number of segments, same last segment: best is the one with
// the most equal segments, then an identical body (first capture wins on ties)
pub fn lookup<'a>(captures: &'a [Capture], method: &str, path: &str, body: &[u8]) -> Option<&'a Capture> {
    let wanted: Vec<&str> = path.split('?').next().unwrap().split('/').collect();
    let mut best: Option<(usize, &Capture)> = None;

    for capture in captures.iter().filter(|c| c.method == method) {
        let segments: Vec<&str> = capture.path.split('/').collect();

        if segments.len() != wanted.len() || segments.last() != wanted.last() {
            continue;
        }

        let score = segments.iter().zip(&wanted).filter(|(a, b)| a == b).count() * 2
            + (capture.body == body) as usize;

        if best.map_or(true, |(s, _)| score > s) {
            best = Some((score, capture));
        }
    }

    best.map(|(_, capture)| capture)
}

// captured status line + headers, with a new body
pub fn with_body(response: &[u8], new_body: &[u8]) -> Vec<u8> {
    let head_end = find(response, b"\r\n\r\n").unwrap_or(response.len());

    let mut result: Vec<u8> = String::from_utf8_lossy(&response[..head_end])
        .split("\r\n")
        .map(|line| match line.split_once(':') {
            Some((key, _)) if key.eq_ignore_ascii_case("content-length") => {
                format!("{}: {}\r\n", key, new_body.len())
            }
            _ => format!("{}\r\n", line),
        })
        .collect::<String>()
        .into_bytes();

    result.extend_from_slice(b"\r\n");
    result.extend_from_slice(new_body);
    result
}

fn read_request(stream: &mut TcpStream) -> Option<Vec<u8>> {
    let mut raw = Vec::new();
    let mut buffer = [0u8; 8192];

    let head_end = loop {
        if let Some(position) = find(&raw, b"\r\n\r\n") {
            break position + 4;
        }
        match stream.read(&mut buffer) {
            Ok(0) | Err(_) => return None,
            Ok(n) => raw.extend_from_slice(&buffer[..n]),
        }
    };

    let content_length = String::from_utf8_lossy(&raw[..head_end])
        .lines()
        .filter_map(|line| line.split_once(':'))
        .find(|(key, _)| key.eq_ignore_ascii_case("content-length"))
        .and_then(|(_, value)| value.trim().parse::<usize>().ok())
        .unwrap_or(0);

    while raw.len() < head_end + content_length {
        match stream.read(&mut buffer) {
            Ok(0) | Err(_) => break,
            Ok(n) => raw.extend_from_slice(&buffer[..n]),
        }
    }

    Some(raw)
}

fn handle(mut stream: TcpStream, captures: &[Capture], state: &Mutex<device::State>) {
    let Some(raw) = read_request(&mut stream) else { return };
    let Some((method, path)) = request_line(&raw) else { return };

    let stateful = state.lock().unwrap().handle(captures, &method, &path, body(&raw));

    if let Some(response) = stateful {
        println!("{} {} -> state", method, path);
        let _ = stream.write_all(&response);
        return;
    }

    match lookup(captures, &method, &path, body(&raw)) {
        Some(capture) => {
            println!("{} {} -> {}", method, path, capture.name);
            let _ = stream.write_all(&capture.response);
        }
        None => {
            println!("{} {} -> 404 (no capture)", method, path);
            let _ = stream.write_all(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n");
        }
    }
    // one request per connection, like the hue bridge (Connection: close)
}

fn main() {
    let port = env::var("PORT").unwrap_or_else(|_| "8000".to_string());
    let dir = env::var("CAPTURES").unwrap_or_else(|_| "captures".to_string());

    let captures = Arc::new(load_captures(&dir));
    for capture in captures.iter() {
        println!("loaded {}: {} {}", capture.name, capture.method, capture.path);
    }

    let state = Arc::new(Mutex::new(device::State::new(&captures)));

    let listener = TcpListener::bind(format!("0.0.0.0:{}", port)).expect("cannot bind");
    println!("listening on :{}", port);

    for stream in listener.incoming().flatten() {
        let captures = Arc::clone(&captures);
        let state = Arc::clone(&state);
        thread::spawn(move || handle(stream, &captures, &state));
    }
}
