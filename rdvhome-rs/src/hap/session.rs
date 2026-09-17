// After pair-verify everything on the connection is encrypted: frames of at
// most 1024 bytes, each one <length: u16 le><ciphertext><tag>, the length is
// the associated data, the nonce counts the frames of each direction.

use chacha20poly1305::aead::{Aead, KeyInit, Payload};
use chacha20poly1305::{ChaCha20Poly1305, Key, Nonce};
use hkdf::Hkdf;
use sha2::Sha512;

const MAX_FRAME: usize = 1024;
const TAG: usize = 16;

pub fn hkdf(key: &[u8], salt: &[u8], info: &[u8]) -> [u8; 32] {
    let mut out = [0u8; 32];
    Hkdf::<Sha512>::new(Some(salt), key).expand(info, &mut out).expect("hkdf");
    out
}

// the fixed nonces of the pairing messages: "PS-Msg05" padded to 12 bytes
pub fn seal(key: &[u8; 32], nonce: &[u8; 8], plaintext: &[u8]) -> Vec<u8> {
    let mut padded = [0u8; 12];
    padded[4..].copy_from_slice(nonce);

    ChaCha20Poly1305::new(Key::from_slice(key)).encrypt(Nonce::from_slice(&padded), plaintext).expect("encrypt")
}

pub fn open(key: &[u8; 32], nonce: &[u8; 8], ciphertext: &[u8]) -> Option<Vec<u8>> {
    let mut padded = [0u8; 12];
    padded[4..].copy_from_slice(nonce);

    ChaCha20Poly1305::new(Key::from_slice(key)).decrypt(Nonce::from_slice(&padded), ciphertext).ok()
}

pub struct Session {
    read: ChaCha20Poly1305,
    write: ChaCha20Poly1305,
    read_count: u64,
    write_count: u64,
    buffer: Vec<u8>,
}

impl Session {
    pub fn new(shared_key: &[u8]) -> Session {
        Session {
            // named from the controller's side: it reads what we write
            write: ChaCha20Poly1305::new(Key::from_slice(&hkdf(shared_key, b"Control-Salt", b"Control-Read-Encryption-Key"))),
            read: ChaCha20Poly1305::new(Key::from_slice(&hkdf(shared_key, b"Control-Salt", b"Control-Write-Encryption-Key"))),
            read_count: 0,
            write_count: 0,
            buffer: Vec::new(),
        }
    }

    fn nonce(count: u64) -> Nonce {
        let mut nonce = [0u8; 12];
        nonce[4..].copy_from_slice(&count.to_le_bytes());
        nonce.into()
    }

    pub fn encrypt(&mut self, data: &[u8]) -> Vec<u8> {
        let mut out = Vec::with_capacity(data.len() + (data.len() / MAX_FRAME + 1) * (2 + TAG));

        for chunk in data.chunks(MAX_FRAME) {
            let length = (chunk.len() as u16).to_le_bytes();
            let sealed = self.write.encrypt(&Self::nonce(self.write_count), Payload { msg: chunk, aad: &length }).expect("encrypt");

            self.write_count += 1;
            out.extend(length);
            out.extend(sealed);
        }

        out
    }

    // Feed what came from the socket, get the plaintext of the complete frames.
    // Err when a frame does not authenticate: the connection must be closed.
    pub fn decrypt(&mut self, data: &[u8]) -> Result<Vec<u8>, ()> {
        self.buffer.extend(data);
        let mut out = Vec::new();

        while self.buffer.len() >= 2 {
            let length = u16::from_le_bytes([self.buffer[0], self.buffer[1]]) as usize;
            let frame = 2 + length + TAG;

            if self.buffer.len() < frame {
                break;
            }

            let opened = self
                .read
                .decrypt(&Self::nonce(self.read_count), Payload { msg: &self.buffer[2..frame], aad: &self.buffer[..2] })
                .map_err(|_| ())?;

            self.read_count += 1;
            out.extend(opened);
            self.buffer.drain(..frame);
        }

        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frames() {
        // the other side: reads with our write key
        let mut accessory = Session::new(&[1; 32]);
        let mut controller = Session::new(&[1; 32]);
        std::mem::swap(&mut controller.read, &mut controller.write);

        let message = vec![42u8; 3000];
        let wire = accessory.encrypt(&message);
        assert_eq!(wire.len(), 3000 + 3 * 18);

        let (first, second) = wire.split_at(1500);
        let mut plain = controller.decrypt(first).unwrap();
        plain.extend(controller.decrypt(second).unwrap());
        assert_eq!(plain, message);
    }
}
