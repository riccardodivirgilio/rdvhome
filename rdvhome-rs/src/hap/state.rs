// What must survive a restart for the paired iPhones to recognise the bridge:
// its id (a fake mac), its ed25519 key, the paired controllers, the config
// number. The file is the `accessory.state` of hap-python, same keys and same
// encoding, so the pairing made with the old app keeps working (and the old
// app can still read a file written here).
//
// `pincode` and `setup_id` are ours: hap-python makes new ones at every start,
// we keep them so that `rdvhome pair` shows the code of the running server.

use std::path::PathBuf;

use ed25519_dalek::SigningKey;
use rand::Rng;
use serde_json::{json, Map, Value};

pub const ADMIN: u8 = 1;

pub struct Controller {
    // the pairing id, a uuid, lowercase like python's str(UUID)
    pub id: String,
    pub public_key: [u8; 32],
    pub permissions: u8,
    // the id exactly as the controller sent it (uppercase for an iPhone)
    pub username: Option<Vec<u8>>,
}

pub struct State {
    path: PathBuf,
    pub mac: String,
    pub config_version: u32,
    pub controllers: Vec<Controller>,
    pub accessories_hash: Option<String>,
    pub key: SigningKey,
    pub pincode: String,
    pub setup_id: String,
}

fn random_from(alphabet: &[u8], length: usize) -> String {
    let mut rng = rand::rng();
    (0..length).map(|_| alphabet[rng.random_range(0..alphabet.len())] as char).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

fn unhex(text: &str) -> Option<Vec<u8>> {
    (text.len() % 2 == 0).then(|| (0..text.len()).step_by(2).map(|i| u8::from_str_radix(text.get(i..i + 2)?, 16).ok()).collect())?
}

impl State {
    pub fn load(path: PathBuf) -> State {
        let saved: Value = std::fs::read(&path).ok().and_then(|raw| serde_json::from_slice(&raw).ok()).unwrap_or(Value::Null);
        let text = |key: &str| saved[key].as_str().map(String::from);

        let key = text("private_key")
            .and_then(|k| unhex(&k))
            .and_then(|k| <[u8; 32]>::try_from(k).ok())
            .map(|k| SigningKey::from_bytes(&k));

        let controllers = saved["paired_clients"]
            .as_object()
            .map(|clients| {
                clients
                    .iter()
                    .filter_map(|(id, public_key)| {
                        Some(Controller {
                            id: id.to_lowercase(),
                            public_key: unhex(public_key.as_str()?)?.try_into().ok()?,
                            permissions: saved["client_properties"][id]["permissions"].as_u64().unwrap_or(ADMIN as u64) as u8,
                            username: saved["client_uuid_to_bytes"][id].as_str().and_then(unhex),
                        })
                    })
                    .collect()
            })
            .unwrap_or_default();

        let pin = random_from(b"0123456789", 8);
        let is_new = key.is_none();

        let state = State {
            path,
            mac: text("mac").unwrap_or_else(|| {
                let digits = random_from(b"0123456789ABCDEF", 12);
                digits.as_bytes().chunks(2).map(|pair| String::from_utf8_lossy(pair).into_owned()).collect::<Vec<_>>().join(":")
            }),
            config_version: saved["config_version"].as_u64().unwrap_or(1) as u32,
            controllers,
            accessories_hash: text("accessories_hash"),
            key: key.unwrap_or_else(|| SigningKey::from_bytes(&rand::rng().random::<[u8; 32]>())),
            pincode: text("pincode").unwrap_or_else(|| format!("{}-{}-{}", &pin[..3], &pin[3..5], &pin[5..])),
            setup_id: text("setup_id").unwrap_or_else(|| random_from(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 4)),
        };

        if is_new || text("pincode").is_none() {
            state.save();
        }

        state
    }

    pub fn save(&self) {
        let per_controller = |value: &dyn Fn(&Controller) -> Option<Value>| -> Map<String, Value> {
            self.controllers.iter().filter_map(|c| Some((c.id.clone(), value(c)?))).collect()
        };

        let saved = json!({
            "mac": self.mac,
            "config_version": self.config_version,
            "paired_clients": per_controller(&|c| Some(json!(hex(&c.public_key)))),
            "client_properties": per_controller(&|c| Some(json!({"permissions": c.permissions}))),
            "accessories_hash": self.accessories_hash,
            "client_uuid_to_bytes": per_controller(&|c| c.username.as_deref().map(|u| json!(hex(u)))),
            "private_key": hex(&self.key.to_bytes()),
            "public_key": hex(self.key.verifying_key().as_bytes()),
            "pincode": self.pincode,
            "setup_id": self.setup_id,
        });

        // never leave half a file: losing it means pairing everything again
        let temporary = self.path.with_extension("state.tmp");
        let written = std::fs::write(&temporary, saved.to_string()).and_then(|_| std::fs::rename(&temporary, &self.path));

        if let Err(e) = written {
            eprintln!("homekit: cannot write {:?}: {}", self.path, e);
        }
    }

    pub fn is_paired(&self) -> bool {
        !self.controllers.is_empty()
    }

    pub fn controller(&self, id: &str) -> Option<&Controller> {
        self.controllers.iter().find(|c| c.id == id)
    }

    pub fn add_controller(&mut self, username: &[u8], public_key: [u8; 32], permissions: u8) {
        let id = String::from_utf8_lossy(username).to_lowercase();

        self.controllers.retain(|c| c.id != id);
        self.controllers.push(Controller { id, public_key, permissions, username: Some(username.to_vec()) });
        self.save();
    }

    pub fn remove_controller(&mut self, id: &str) {
        self.controllers.retain(|c| c.id != id);

        // without an admin nobody could manage the pairings any more
        if !self.controllers.iter().any(|c| c.permissions & ADMIN != 0) {
            self.controllers.clear();
        }

        self.save();
    }

    // true when the accessories changed since the last start: the controllers
    // see the new config number and read them again
    pub fn set_accessories_hash(&mut self, hash: String) -> bool {
        if self.accessories_hash.as_deref() == Some(&hash) {
            return false;
        }

        self.accessories_hash = Some(hash);
        self.config_version = if self.config_version >= 65535 { 1 } else { self.config_version + 1 };
        self.save();
        true
    }

    // X-HM://..., what the qr code says: category, "ip" flag, the setup code, the setup id
    pub fn setup_uri(&self, category: u64) -> String {
        let code: u64 = self.pincode.replace('-', "").parse().unwrap_or(0);
        let mut payload = (category & 0xff) << 31 | 2 << 27 | (code & 0x7ffffff);
        let mut encoded = Vec::new();

        while payload > 0 {
            encoded.push(b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[(payload % 36) as usize]);
            payload /= 36;
        }

        while encoded.len() < 9 {
            encoded.push(b'0');
        }

        encoded.reverse();
        format!("X-HM://{}{}", String::from_utf8_lossy(&encoded), self.setup_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn setup_uri_like_hap_python() {
        let mut state = State::load(std::env::temp_dir().join("rdvhome-test-missing").join("accessory.state"));
        state.pincode = "340-99-237".to_string();
        state.setup_id = "QHE7".to_string();

        assert_eq!(state.setup_uri(2), "X-HM://002418F8LQHE7");
    }
}
