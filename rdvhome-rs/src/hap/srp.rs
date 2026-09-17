// SRP-6a, accessory side, as HomeKit wants it: the 3072 bit group of RFC 5054,
// SHA-512, user "Pair-Setup", the password is the setup code (xxx-xx-xxx).

use num_bigint::BigUint;
use sha2::{Digest, Sha512};

const N_HEX: &str = "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08\
8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B\
302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9\
A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE6\
49286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8\
FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D\
670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C\
180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF695581718\
3995497CEA956AE515D2261898FA051015728E5A8AAAC42DAD33170D\
04507A33A85521ABDF1CBA64ECFB850458DBEF0A8AEA71575D060C7D\
B3970F85A6E1E4C7ABF5AE8CDB0933D71E8C94E04A25619DCEE3D226\
1AD2EE6BF12FFA06D98A0864D87602733EC86A64521F2B18177B200C\
BBE117577A615D6C770988C0BAD946E208E24FA074E5AB3143DB5BFC\
E0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF";

const N_BYTES: usize = 384;
const USER: &[u8] = b"Pair-Setup";

fn hash(parts: &[&[u8]]) -> Vec<u8> {
    let mut hasher = Sha512::new();
    for part in parts {
        hasher.update(part);
    }
    hasher.finalize().to_vec()
}

fn pad(value: &[u8]) -> Vec<u8> {
    let mut out = vec![0; N_BYTES.saturating_sub(value.len())];
    out.extend(value);
    out
}

pub struct Server {
    n: BigUint,
    salt: [u8; 16],
    verifier: BigUint,
    secret: BigUint,
    public: Vec<u8>,
    // the session key, once the controller sent its public key
    key: Option<Vec<u8>>,
    expected_proof: Vec<u8>,
    answer_proof: Vec<u8>,
}

impl Server {
    pub fn new(password: &[u8], salt: [u8; 16], secret: [u8; 32]) -> Server {
        let n = BigUint::parse_bytes(N_HEX.as_bytes(), 16).expect("prime");
        let g = BigUint::from(5u8);

        let x = BigUint::from_bytes_be(&hash(&[&salt, &hash(&[USER, b":", password])]));
        let verifier = g.modpow(&x, &n);

        let k = BigUint::from_bytes_be(&hash(&[&n.to_bytes_be(), &pad(&g.to_bytes_be())]));
        let secret = BigUint::from_bytes_be(&secret);
        let public = ((k * &verifier + g.modpow(&secret, &n)) % &n).to_bytes_be();

        Server { n, salt, verifier, secret, public, key: None, expected_proof: Vec::new(), answer_proof: Vec::new() }
    }

    pub fn salt(&self) -> &[u8] {
        &self.salt
    }

    pub fn public(&self) -> &[u8] {
        &self.public
    }

    // A, the public key of the controller. False when it is not acceptable.
    pub fn set_client_public(&mut self, client_public: &[u8]) -> bool {
        let a = BigUint::from_bytes_be(client_public);

        if (&a % &self.n) == BigUint::from(0u8) {
            return false;
        }

        let u = BigUint::from_bytes_be(&hash(&[&pad(client_public), &pad(&self.public)]));
        let premaster = (a * self.verifier.modpow(&u, &self.n)).modpow(&self.secret, &self.n);
        let key = hash(&[&premaster.to_bytes_be()]);

        let g = BigUint::from(5u8);
        let group: Vec<u8> = hash(&[&self.n.to_bytes_be()]).iter().zip(hash(&[&g.to_bytes_be()])).map(|(a, b)| a ^ b).collect();

        self.expected_proof = hash(&[&group, &hash(&[USER]), &self.salt, client_public, &self.public, &key]);
        self.answer_proof = hash(&[client_public, &self.expected_proof, &key]);
        self.key = Some(key);
        true
    }

    // The controller proves it knows the setup code; the answer proves we do.
    pub fn verify(&self, proof: &[u8]) -> Option<&[u8]> {
        (self.key.is_some() && proof == self.expected_proof).then_some(&self.answer_proof)
    }

    pub fn session_key(&self) -> Option<&[u8]> {
        self.key.as_deref()
    }
}
