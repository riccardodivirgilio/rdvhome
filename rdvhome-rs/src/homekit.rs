// HomeKit bridge: not ported yet (phase 5 of knowledge/RDVHOME-RS.md).
// Until then /homekit and /qrcode answer 500.

pub struct Pairing {
    pub paircode: String,
    pub uri: String,
}

impl Pairing {
    pub fn qrcode_svg(&self) -> String {
        String::new()
    }
}

pub fn pairing() -> Option<Pairing> {
    None
}
