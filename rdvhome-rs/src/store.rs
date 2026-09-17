// One json file per key (remote-led_tv.json, gpio-4.json), same names and
// layout as rdvhome/utils/keystore.py so the data folder of the old app keeps working.

use std::path::PathBuf;

use serde::{de::DeserializeOwned, Serialize};

use crate::json::dumps;

#[derive(Clone)]
pub struct Store {
    path: PathBuf,
    prefix: &'static str,
}

// RDV_DATA_DIR, or ~/.rdvhome on the raspberry, or ./data while developing
pub fn data_dir(simulated: bool) -> PathBuf {
    if let Some(path) = std::env::var_os("RDV_DATA_DIR") {
        return PathBuf::from(path);
    }

    match (simulated, std::env::var_os("HOME")) {
        (false, Some(home)) => PathBuf::from(home).join(".rdvhome"),
        _ => PathBuf::from("data"),
    }
}

impl Store {
    pub fn new(path: PathBuf, prefix: &'static str) -> Store {
        let _ = std::fs::create_dir_all(&path);
        Store { path, prefix }
    }

    fn file(&self, key: &str) -> PathBuf {
        self.path.join(format!("{}-{}.json", self.prefix, key))
    }

    pub fn get<T: DeserializeOwned>(&self, key: &str) -> Option<T> {
        serde_json::from_slice(&std::fs::read(self.file(key)).ok()?).ok()
    }

    pub fn set<T: Serialize>(&self, key: &str, value: &T) {
        if let Err(e) = std::fs::write(self.file(key), dumps(value)) {
            eprintln!("store: cannot write {:?}: {}", self.file(key), e);
        }
    }
}
