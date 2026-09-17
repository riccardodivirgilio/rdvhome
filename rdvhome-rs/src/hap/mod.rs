// HomeKit Accessory Protocol over ip, the accessory side: what hap-python did
// for the old app. Only what a bridge of switches and lightbulbs needs:
//
//   POST /pair-setup       SRP with the setup code, then the long term keys are exchanged
//   POST /pair-verify      a paired controller opens an encrypted session
//   GET  /accessories      the database
//   GET  /characteristics  values
//   PUT  /characteristics  write values, subscribe to events
//   PUT  /prepare          timed writes (accepted, not enforced)
//   POST /pairings         add / remove / list controllers (admins only)
//
// plus the EVENT messages to the subscribed controllers and the _hap._tcp
// advertisement. The rest of the app sees `Hap`: set_value() when something
// changed in the house, and a `Writes` channel with what the controllers ask.

pub mod accessory;
mod session;
mod srp;
pub mod state;
mod tlv;

use std::collections::HashSet;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use ed25519_dalek::{Signature, Signer, Verifier, VerifyingKey};
use rand::Rng;
use serde_json::{json, Value};
use sha2::{Digest, Sha512};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::mpsc;
use x25519_dalek::{PublicKey, StaticSecret};

use accessory::Accessory;
use session::{hkdf, open, seal, Session};
use state::{State, ADMIN};
use tlv::Tlv;

pub const CATEGORY_BRIDGE: u64 = 2;

const STATUS_INSUFFICIENT_PRIVILEGES: i64 = -70401;
const STATUS_READ_ONLY: i64 = -70404;
const STATUS_WRITE_ONLY: i64 = -70405;
const STATUS_NOTIFICATION_NOT_SUPPORTED: i64 = -70406;
const STATUS_DOES_NOT_EXIST: i64 = -70409;
const STATUS_INVALID_VALUE: i64 = -70410;

// a controller wrote a value: (aid, iid, value)
pub type Write = (u64, u64, Value);

struct Connection {
    id: u64,
    // pairing id, once verified
    controller: Option<String>,
    subscriptions: HashSet<(u64, u64)>,
    // EVENT messages to push (plaintext), None closes the connection
    events: mpsc::UnboundedSender<Option<Vec<u8>>>,
}

pub struct Hap {
    name: String,
    port: u16,
    pub state: Mutex<State>,
    accessories: Mutex<Vec<Accessory>>,
    connections: Mutex<Vec<Connection>>,
    // one pair-setup at a time
    setup: Mutex<Option<srp::Server>>,
    writes: mpsc::UnboundedSender<Write>,
    mdns: Mutex<Option<mdns_sd::ServiceDaemon>>,
    next_connection: AtomicU64,
}

struct Response {
    status: u16,
    content_type: &'static str,
    body: Vec<u8>,
    // pair-verify completed: encrypt from the next message on
    upgrade: Option<Vec<u8>>,
}

impl Response {
    fn tlv(items: &[(u8, &[u8])]) -> Response {
        Response { status: 200, content_type: "application/pairing+tlv8", body: tlv::encode(items), upgrade: None }
    }

    fn tlv_error(state: u8, error: u8) -> Response {
        Response::tlv(&[(tlv::STATE, &[state]), (tlv::ERROR, &[error])])
    }

    fn json(status: u16, body: Value) -> Response {
        Response { status, content_type: "application/hap+json", body: body.to_string().into_bytes(), upgrade: None }
    }

    fn status(status: u16, hap_status: i64) -> Response {
        Response::json(status, json!({"status": hap_status}))
    }

    fn to_bytes(&self) -> Vec<u8> {
        let reason = match self.status {
            200 => "OK",
            204 => "No Content",
            207 => "Multi-Status",
            400 => "Bad Request",
            401 => "Unauthorized",
            404 => "Not Found",
            _ => "Internal Server Error",
        };

        let mut out = format!("HTTP/1.1 {} {}\r\n", self.status, reason).into_bytes();

        if self.status != 204 {
            out.extend(format!("Content-Type: {}\r\nContent-Length: {}\r\n", self.content_type, self.body.len()).bytes());
        }

        out.extend(b"\r\n");
        out.extend(&self.body);
        out
    }
}

struct Request {
    method: String,
    path: String,
    query: String,
    body: Vec<u8>,
}

// One http request out of the buffer, when it is all there.
fn take_request(buffer: &mut Vec<u8>) -> Option<Request> {
    let head_end = buffer.windows(4).position(|w| w == b"\r\n\r\n")? + 4;
    let head = String::from_utf8_lossy(&buffer[..head_end]).into_owned();
    let mut lines = head.split("\r\n");

    let mut request_line = lines.next()?.split(' ');
    let (method, target) = (request_line.next()?.to_string(), request_line.next()?.to_string());

    let length: usize = lines
        .filter_map(|line| line.split_once(':'))
        .find(|(name, _)| name.eq_ignore_ascii_case("content-length"))
        .and_then(|(_, value)| value.trim().parse().ok())
        .unwrap_or(0);

    if buffer.len() < head_end + length {
        return None;
    }

    let body = buffer[head_end..head_end + length].to_vec();
    buffer.drain(..head_end + length);

    let (path, query) = target.split_once('?').unwrap_or((&target, ""));
    Some(Request { method, path: path.to_string(), query: query.to_string(), body })
}

// state of one connection while it pairs / verifies
#[derive(Default)]
struct Handshake {
    // pair-verify M1: (our session public key, controller's session public key, shared secret, key of the handshake)
    verify: Option<([u8; 32], [u8; 32], [u8; 32], [u8; 32])>,
}

impl Hap {
    pub fn new(name: &str, port: u16, state: State, accessories: Vec<Accessory>) -> (Arc<Hap>, mpsc::UnboundedReceiver<Write>) {
        let (writes, written) = mpsc::unbounded_channel();

        let hap = Arc::new(Hap {
            name: name.to_string(),
            port,
            state: Mutex::new(state),
            accessories: Mutex::new(accessories),
            connections: Mutex::default(),
            setup: Mutex::default(),
            writes,
            mdns: Mutex::default(),
            next_connection: AtomicU64::new(1),
        });

        let hash = hap.accessories_hash();
        if hap.state.lock().unwrap().set_accessories_hash(hash) {
            println!("homekit: the accessories changed, config number is now {}", hap.state.lock().unwrap().config_version);
        }

        (hap, written)
    }

    fn accessories_json(&self, with_values: bool) -> Value {
        let accessories: Vec<Value> = self.accessories.lock().unwrap().iter().map(|a| a.to_json(with_values)).collect();
        json!({"accessories": accessories})
    }

    fn accessories_hash(&self) -> String {
        let canonical = accessory::sorted(&self.accessories_json(false)).to_string();
        Sha512::digest(canonical.as_bytes()).iter().map(|b| format!("{:02x}", b)).collect()
    }

    pub fn setup_uri(&self) -> String {
        self.state.lock().unwrap().setup_uri(CATEGORY_BRIDGE)
    }

    pub fn pincode(&self) -> String {
        self.state.lock().unwrap().pincode.clone()
    }

    // Something changed in the house: remember it and tell who subscribed.
    pub fn set_value(&self, aid: u64, iid: u64, value: Value) {
        self.update(aid, iid, value, None);
    }

    fn update(&self, aid: u64, iid: u64, value: Value, except: Option<u64>) {
        {
            let mut accessories = self.accessories.lock().unwrap();
            let Some(characteristic) = accessories.iter_mut().find(|a| a.aid == aid).and_then(|a| a.characteristic(iid)) else { return };
            let Some(value) = characteristic.valid(&value) else { return };

            if characteristic.value.as_ref() == Some(&value) {
                return;
            }

            characteristic.value = Some(value.clone());

            let body = json!({"characteristics": [{"aid": aid, "iid": iid, "value": value}]}).to_string();
            let event = format!("EVENT/1.0 200 OK\r\nContent-Type: application/hap+json\r\nContent-Length: {}\r\n\r\n{}", body.len(), body);

            for connection in self.connections.lock().unwrap().iter() {
                if Some(connection.id) != except && connection.subscriptions.contains(&(aid, iid)) {
                    let _ = connection.events.send(Some(event.clone().into_bytes()));
                }
            }
        }
    }

    // ---- pairing ----

    fn pair_setup(&self, request: &Tlv) -> Response {
        if self.state.lock().unwrap().is_paired() {
            return Response::tlv_error(2, tlv::ERROR_UNAVAILABLE);
        }

        match request.get(tlv::STATE) {
            Some([1]) => {
                let mut rng = rand::rng();
                let server = srp::Server::new(self.pincode().as_bytes(), rng.random(), rng.random());
                let response = Response::tlv(&[(tlv::STATE, &[2]), (tlv::SALT, server.salt()), (tlv::PUBLIC_KEY, server.public())]);

                *self.setup.lock().unwrap() = Some(server);
                response
            }

            Some([3]) => {
                let mut setup = self.setup.lock().unwrap();
                let (Some(server), Some(public), Some(proof)) = (setup.as_mut(), request.get(tlv::PUBLIC_KEY), request.get(tlv::PROOF)) else {
                    return Response::tlv_error(4, tlv::ERROR_AUTHENTICATION);
                };

                // a wrong proof is a wrong setup code
                match server.set_client_public(public).then(|| server.verify(proof)).flatten() {
                    Some(answer) => Response::tlv(&[(tlv::STATE, &[4]), (tlv::PROOF, answer)]),
                    None => Response::tlv_error(4, tlv::ERROR_AUTHENTICATION),
                }
            }

            Some([5]) => self.pair_setup_exchange(request).unwrap_or_else(|| Response::tlv_error(6, tlv::ERROR_AUTHENTICATION)),

            _ => Response::status(400, STATUS_INVALID_VALUE),
        }
    }

    // M5 / M6: the controller gives its long term public key, we give ours
    fn pair_setup_exchange(&self, request: &Tlv) -> Option<Response> {
        let session_key = self.setup.lock().unwrap().as_ref()?.session_key()?.to_vec();
        let key = hkdf(&session_key, b"Pair-Setup-Encrypt-Salt", b"Pair-Setup-Encrypt-Info");

        let inner = Tlv::decode(&open(&key, b"PS-Msg05", request.get(tlv::ENCRYPTED_DATA)?)?);
        let (username, public_key, signature) = (inner.get(tlv::IDENTIFIER)?, inner.get(tlv::PUBLIC_KEY)?, inner.get(tlv::SIGNATURE)?);

        let public_key: [u8; 32] = public_key.try_into().ok()?;
        let mut material = hkdf(&session_key, b"Pair-Setup-Controller-Sign-Salt", b"Pair-Setup-Controller-Sign-Info").to_vec();
        material.extend(username);
        material.extend(public_key);

        VerifyingKey::from_bytes(&public_key).ok()?.verify(&material, &Signature::from_slice(signature).ok()?).ok()?;

        let mut state = self.state.lock().unwrap();
        let mut material = hkdf(&session_key, b"Pair-Setup-Accessory-Sign-Salt", b"Pair-Setup-Accessory-Sign-Info").to_vec();
        material.extend(state.mac.bytes());
        material.extend(state.key.verifying_key().as_bytes());

        let answer = tlv::encode(&[
            (tlv::IDENTIFIER, state.mac.as_bytes()),
            (tlv::PUBLIC_KEY, state.key.verifying_key().as_bytes()),
            (tlv::SIGNATURE, &state.key.sign(&material).to_bytes()),
        ]);

        state.add_controller(username, public_key, ADMIN);
        println!("homekit: paired with {}", String::from_utf8_lossy(username));
        *self.setup.lock().unwrap() = None;

        Some(Response::tlv(&[(tlv::STATE, &[6]), (tlv::ENCRYPTED_DATA, &seal(&key, b"PS-Msg06", &answer))]))
    }

    fn pair_verify(&self, request: &Tlv, handshake: &mut Handshake, controller: &mut Option<String>) -> Response {
        let state = self.state.lock().unwrap();

        match request.get(tlv::STATE) {
            Some([1]) if state.is_paired() => {
                let Some(their_public) = request.get(tlv::PUBLIC_KEY).and_then(|k| <[u8; 32]>::try_from(k).ok()) else {
                    return Response::tlv_error(2, tlv::ERROR_AUTHENTICATION);
                };

                let secret = StaticSecret::from(rand::rng().random::<[u8; 32]>());
                let our_public = PublicKey::from(&secret).to_bytes();
                let shared = secret.diffie_hellman(&PublicKey::from(their_public)).to_bytes();
                let key = hkdf(&shared, b"Pair-Verify-Encrypt-Salt", b"Pair-Verify-Encrypt-Info");

                let material = [&our_public[..], state.mac.as_bytes(), &their_public[..]].concat();
                let proof = tlv::encode(&[(tlv::IDENTIFIER, state.mac.as_bytes()), (tlv::SIGNATURE, &state.key.sign(&material).to_bytes())]);

                handshake.verify = Some((our_public, their_public, shared, key));

                Response::tlv(&[(tlv::STATE, &[2]), (tlv::ENCRYPTED_DATA, &seal(&key, b"PV-Msg02", &proof)), (tlv::PUBLIC_KEY, &our_public)])
            }

            Some([3]) => {
                let verified = (|| {
                    let (our_public, their_public, shared, key) = handshake.verify.take()?;
                    let inner = Tlv::decode(&open(&key, b"PV-Msg03", request.get(tlv::ENCRYPTED_DATA)?)?);
                    let username = inner.get(tlv::IDENTIFIER)?;
                    let id = String::from_utf8_lossy(username).to_lowercase();

                    let material = [&their_public[..], username, &our_public[..]].concat();
                    let signature = Signature::from_slice(inner.get(tlv::SIGNATURE)?).ok()?;
                    VerifyingKey::from_bytes(&state.controller(&id)?.public_key).ok()?.verify(&material, &signature).ok()?;

                    Some((id, shared))
                })();

                match verified {
                    Some((id, shared)) => {
                        *controller = Some(id);
                        Response { upgrade: Some(shared.to_vec()), ..Response::tlv(&[(tlv::STATE, &[4])]) }
                    }
                    None => Response::tlv_error(4, tlv::ERROR_AUTHENTICATION),
                }
            }

            _ => Response::tlv_error(2, tlv::ERROR_AUTHENTICATION),
        }
    }

    fn pairings(&self, request: &Tlv, controller: &str) -> Response {
        let mut state = self.state.lock().unwrap();

        if !state.controller(controller).is_some_and(|c| c.permissions & ADMIN != 0) {
            return Response::tlv_error(2, tlv::ERROR_AUTHENTICATION);
        }

        match request.get(tlv::METHOD) {
            // add
            Some([3]) => {
                let added = (|| {
                    let public_key: [u8; 32] = request.get(tlv::PUBLIC_KEY)?.try_into().ok()?;
                    state.add_controller(request.get(tlv::IDENTIFIER)?, public_key, *request.get(tlv::PERMISSIONS)?.first()?);
                    Some(())
                })();

                match added {
                    Some(()) => Response::tlv(&[(tlv::STATE, &[2])]),
                    None => Response::tlv_error(2, tlv::ERROR_AUTHENTICATION),
                }
            }

            // remove: fine also when it is not there
            Some([4]) => {
                let id = String::from_utf8_lossy(request.get(tlv::IDENTIFIER).unwrap_or_default()).to_lowercase();
                state.remove_controller(&id);
                println!("homekit: removed the pairing with {}", id);

                // its sessions end here, and with nobody left we are discoverable again
                let paired: Vec<String> = state.controllers.iter().map(|c| c.id.clone()).collect();
                for connection in self.connections.lock().unwrap().iter() {
                    if connection.controller.as_ref().is_some_and(|c| !paired.contains(c)) && connection.controller.as_deref() != Some(controller) {
                        let _ = connection.events.send(None);
                    }
                }

                Response::tlv(&[(tlv::STATE, &[2])])
            }

            // list
            Some([5]) => {
                let mut items: Vec<(u8, Vec<u8>)> = vec![(tlv::STATE, vec![2])];

                for (n, c) in state.controllers.iter().enumerate() {
                    if n > 0 {
                        items.push((tlv::SEPARATOR, Vec::new()));
                    }
                    // an iPhone wants its id back as it sent it (uppercase)
                    items.push((tlv::IDENTIFIER, c.username.clone().unwrap_or_else(|| c.id.to_uppercase().into_bytes())));
                    items.push((tlv::PUBLIC_KEY, c.public_key.to_vec()));
                    items.push((tlv::PERMISSIONS, vec![c.permissions & ADMIN]));
                }

                let items: Vec<(u8, &[u8])> = items.iter().map(|(tag, value)| (*tag, value.as_slice())).collect();
                Response::tlv(&items)
            }

            _ => Response::status(400, STATUS_INVALID_VALUE),
        }
    }

    // ---- characteristics ----

    fn read_characteristics(&self, query: &str) -> Response {
        let ids = query.split('&').find_map(|pair| pair.strip_prefix("id=")).unwrap_or("");
        let mut accessories = self.accessories.lock().unwrap();
        let mut failed = false;

        let mut results: Vec<Value> = ids
            .split(',')
            .filter_map(|id| {
                let (aid, iid) = id.split_once('.')?;
                let (aid, iid): (u64, u64) = (aid.parse().ok()?, iid.parse().ok()?);

                let characteristic = accessories.iter_mut().find(|a| a.aid == aid).and_then(|a| a.characteristic(iid));
                let status = match &characteristic {
                    None => STATUS_DOES_NOT_EXIST,
                    Some(c) if !c.can("pr") => STATUS_WRITE_ONLY,
                    Some(_) => 0,
                };

                failed |= status != 0;

                Some(match (status, characteristic) {
                    (0, Some(c)) => json!({"aid": aid, "iid": iid, "status": 0, "value": c.value}),
                    _ => json!({"aid": aid, "iid": iid, "status": status}),
                })
            })
            .collect();

        // the status is only there when something failed
        if !failed {
            for result in &mut results {
                result.as_object_mut().unwrap().remove("status");
            }
        }

        Response::json(if failed { 207 } else { 200 }, json!({"characteristics": results}))
    }

    fn write_characteristics(&self, body: &[u8], connection: u64) -> Response {
        let Ok(request) = serde_json::from_slice::<Value>(body) else { return Response::status(400, STATUS_INVALID_VALUE) };
        let mut results = Vec::new();
        let mut failed = false;

        for item in request["characteristics"].as_array().map(Vec::as_slice).unwrap_or_default() {
            let (Some(aid), Some(iid)) = (item["aid"].as_u64(), item["iid"].as_u64()) else { continue };
            let mut status = 0;

            // look, decide, and let go of the lock: update() takes it again
            let checked = {
                let mut accessories = self.accessories.lock().unwrap();
                accessories.iter_mut().find(|a| a.aid == aid).and_then(|a| a.characteristic(iid)).map(|c| {
                    (c.can("ev"), c.can("pw"), item.get("value").map(|v| c.valid(v)))
                })
            };

            match checked {
                None => status = STATUS_DOES_NOT_EXIST,
                Some((can_notify, can_write, value)) => {
                    if let Some(subscribe) = item["ev"].as_bool() {
                        if can_notify {
                            if let Some(c) = self.connections.lock().unwrap().iter_mut().find(|c| c.id == connection) {
                                if subscribe {
                                    c.subscriptions.insert((aid, iid));
                                } else {
                                    c.subscriptions.remove(&(aid, iid));
                                }
                            }
                        } else {
                            status = STATUS_NOTIFICATION_NOT_SUPPORTED;
                        }
                    }

                    match value {
                        None => {}
                        Some(_) if !can_write => status = STATUS_READ_ONLY,
                        Some(None) => status = STATUS_INVALID_VALUE,
                        Some(Some(value)) => {
                            // the other controllers hear about it, the house does it
                            self.update(aid, iid, value.clone(), Some(connection));
                            let _ = self.writes.send((aid, iid, value));
                        }
                    }
                }
            }

            failed |= status != 0;
            results.push(json!({"aid": aid, "iid": iid, "status": status}));
        }

        if failed {
            Response::json(207, json!({"characteristics": results}))
        } else {
            Response { status: 204, content_type: "", body: Vec::new(), upgrade: None }
        }
    }

    fn handle(&self, request: &Request, connection: u64, handshake: &mut Handshake, controller: &mut Option<String>) -> Response {
        let open_paths = matches!(request.path.as_str(), "/pair-setup" | "/pair-verify");

        let Some(verified) = controller.clone().filter(|_| !open_paths) else {
            return match (request.method.as_str(), request.path.as_str()) {
                ("POST", "/pair-setup") => self.pair_setup(&Tlv::decode(&request.body)),
                ("POST", "/pair-verify") => self.pair_verify(&Tlv::decode(&request.body), handshake, controller),
                ("POST", "/pairings") => Response::tlv_error(2, tlv::ERROR_AUTHENTICATION),
                _ => Response::status(401, STATUS_INSUFFICIENT_PRIVILEGES),
            };
        };

        match (request.method.as_str(), request.path.as_str()) {
            ("GET", "/accessories") => Response::json(200, self.accessories_json(true)),
            ("GET", "/characteristics") => self.read_characteristics(&request.query),
            ("PUT", "/characteristics") => self.write_characteristics(&request.body, connection),
            ("PUT", "/prepare") => Response::json(200, json!({"status": 0})),
            ("POST", "/pairings") => {
                let response = self.pairings(&Tlv::decode(&request.body), &verified);
                self.advertise();
                response
            }
            _ => Response::status(404, STATUS_DOES_NOT_EXIST),
        }
    }

    // ---- connections ----

    async fn serve_connection(self: Arc<Self>, mut socket: TcpStream) {
        let id = self.next_connection.fetch_add(1, Ordering::SeqCst);
        let (events, mut pushed) = mpsc::unbounded_channel();

        self.connections.lock().unwrap().push(Connection { id, controller: None, subscriptions: HashSet::new(), events });

        let mut session: Option<Session> = None;
        let mut handshake = Handshake::default();
        let mut controller: Option<String> = None;
        let mut buffer = Vec::new();
        let mut chunk = [0u8; 4096];

        'connection: loop {
            tokio::select! {
                read = socket.read(&mut chunk) => {
                    let Ok(read @ 1..) = read else { break };

                    match session.as_mut() {
                        Some(session) => match session.decrypt(&chunk[..read]) {
                            Ok(plain) => buffer.extend(plain),
                            Err(()) => break,
                        },
                        None => buffer.extend(&chunk[..read]),
                    }

                    while let Some(request) = take_request(&mut buffer) {
                        let was_paired = self.state.lock().unwrap().is_paired();
                        let response = self.handle(&request, id, &mut handshake, &mut controller);

                        let bytes = response.to_bytes();
                        let bytes = session.as_mut().map_or(bytes.clone(), |s| s.encrypt(&bytes));

                        if socket.write_all(&bytes).await.is_err() {
                            break 'connection;
                        }

                        // only after the answer went out in clear
                        if let Some(shared) = response.upgrade {
                            session = Some(Session::new(&shared));

                            if let Some(c) = self.connections.lock().unwrap().iter_mut().find(|c| c.id == id) {
                                c.controller = controller.clone();
                            }
                        }

                        // and only after the last pair-setup answer: an iPhone that sees
                        // "paired" in the advertisement too early gives up
                        if was_paired != self.state.lock().unwrap().is_paired() {
                            self.advertise();
                        }
                    }
                }

                event = pushed.recv() => {
                    let Some(Some(event)) = event else { break };

                    if let Some(session) = session.as_mut() {
                        if socket.write_all(&session.encrypt(&event)).await.is_err() {
                            break;
                        }
                    }
                }
            }
        }

        self.connections.lock().unwrap().retain(|c| c.id != id);
    }

    pub async fn serve(self: Arc<Self>) -> std::io::Result<()> {
        let listener = TcpListener::bind(("0.0.0.0", self.port)).await?;
        self.advertise();

        loop {
            let (socket, _) = listener.accept().await?;
            let _ = socket.set_nodelay(true);
            tokio::spawn(self.clone().serve_connection(socket));
        }
    }

    // _hap._tcp: who we are, the config number, and if we can be paired (sf=1)
    fn advertise(&self) {
        let state = self.state.lock().unwrap();
        let short_mac = state.mac[state.mac.len().saturating_sub(8)..].replace(':', "");

        let setup_hash = Sha512::digest(format!("{}{}", state.setup_id, state.mac).as_bytes());
        let properties = [
            ("md", self.name.clone()),
            ("pv", "1.1".to_string()),
            ("id", state.mac.clone()),
            ("c#", state.config_version.to_string()),
            ("s#", "1".to_string()),
            ("ff", "0".to_string()),
            ("ci", CATEGORY_BRIDGE.to_string()),
            ("sf", if state.is_paired() { "0" } else { "1" }.to_string()),
            ("sh", base64(&setup_hash[..4])),
        ];

        let mut mdns = self.mdns.lock().unwrap();

        if mdns.is_none() {
            *mdns = mdns_sd::ServiceDaemon::new().map_err(|e| eprintln!("homekit: mdns: {}", e)).ok();
        }

        let Some(daemon) = mdns.as_ref() else { return };

        let info = mdns_sd::ServiceInfo::new(
            "_hap._tcp.local.",
            &format!("{} {}", self.name, short_mac),
            &format!("{}-{}.local.", self.name, short_mac),
            "",
            self.port,
            &properties[..],
        );

        // registering again replaces the announcement
        match info.map(|info| info.enable_addr_auto()) {
            Ok(info) => drop(daemon.register(info).map_err(|e| eprintln!("homekit: mdns: {}", e))),
            Err(e) => eprintln!("homekit: mdns: {}", e),
        }
    }
}

fn base64(bytes: &[u8]) -> String {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::new();

    for chunk in bytes.chunks(3) {
        let n = chunk.iter().enumerate().fold(0u32, |n, (i, b)| n | (*b as u32) << (16 - 8 * i));

        for i in 0..4 {
            out.push(if i <= chunk.len() { ALPHABET[(n >> (18 - 6 * i) & 63) as usize] as char } else { '=' });
        }
    }

    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn base64_with_padding() {
        assert_eq!(base64(b"abcd"), "YWJjZA==");
        assert_eq!(base64(b"abc"), "YWJj");
    }
}
