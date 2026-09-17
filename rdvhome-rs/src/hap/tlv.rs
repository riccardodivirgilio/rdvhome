// TLV8, the encoding of the pairing messages: tag, length, value. A value
// longer than 255 bytes continues in the next item with the same tag.

pub const METHOD: u8 = 0x00;
pub const IDENTIFIER: u8 = 0x01;
pub const SALT: u8 = 0x02;
pub const PUBLIC_KEY: u8 = 0x03;
pub const PROOF: u8 = 0x04;
pub const ENCRYPTED_DATA: u8 = 0x05;
pub const STATE: u8 = 0x06;
pub const ERROR: u8 = 0x07;
pub const SIGNATURE: u8 = 0x0a;
pub const PERMISSIONS: u8 = 0x0b;
pub const SEPARATOR: u8 = 0xff;

pub const ERROR_AUTHENTICATION: u8 = 0x02;
pub const ERROR_UNAVAILABLE: u8 = 0x06;

pub fn encode(items: &[(u8, &[u8])]) -> Vec<u8> {
    let mut out = Vec::new();

    for (tag, value) in items {
        if value.is_empty() {
            out.extend([*tag, 0]);
        }

        for chunk in value.chunks(255) {
            out.extend([*tag, chunk.len() as u8]);
            out.extend(chunk);
        }
    }

    out
}

pub struct Tlv(Vec<(u8, Vec<u8>)>);

impl Tlv {
    pub fn decode(mut data: &[u8]) -> Tlv {
        let mut items: Vec<(u8, Vec<u8>)> = Vec::new();
        let mut continues = false;

        while data.len() >= 2 {
            let (tag, length) = (data[0], data[1] as usize);
            let value = &data[2..(2 + length).min(data.len())];

            match items.last_mut() {
                Some((last, whole)) if continues && *last == tag => whole.extend(value),
                _ => items.push((tag, value.to_vec())),
            }

            continues = length == 255;
            data = &data[2 + value.len()..];
        }

        Tlv(items)
    }

    pub fn get(&self, tag: u8) -> Option<&[u8]> {
        self.0.iter().find(|(t, _)| *t == tag).map(|(_, v)| v.as_slice())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn long_values_are_split_and_joined() {
        let long = vec![7u8; 600];
        let encoded = encode(&[(STATE, &[1]), (PUBLIC_KEY, &long), (SEPARATOR, &[])]);

        assert_eq!(encoded.len(), 3 + 600 + 3 * 2 + 2);

        let decoded = Tlv::decode(&encoded);
        assert_eq!(decoded.get(STATE), Some(&[1u8][..]));
        assert_eq!(decoded.get(PUBLIC_KEY), Some(&long[..]));
        assert_eq!(decoded.get(SEPARATOR), Some(&[][..]));
    }
}
