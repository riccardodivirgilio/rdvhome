// Colours are hue / saturation / brightness in 0..1, each one optional: a
// request can change only the hue. Conversions follow rdvhome/utils/colors.py
// and the python `colour` library, operation by operation, so the floats match.

use rand::Rng;

use crate::color_names::NAMES;

const FLOAT_ERROR: f64 = 0.0000005;

#[derive(Clone, Copy, Debug, Default)]
pub struct Hsb {
    pub hue: Option<f64>,
    pub saturation: Option<f64>,
    pub brightness: Option<f64>,
}

pub enum ColorError {
    // not a colour name
    Invalid,
    // the python app crashes (500) on a malformed #hex and on black
    Crash,
}

impl Hsb {
    pub fn new(hue: f64, saturation: f64, brightness: f64) -> Hsb {
        Hsb { hue: Some(hue), saturation: Some(saturation), brightness: Some(brightness) }
    }

    pub fn is_empty(&self) -> bool {
        self.hue.is_none() && self.saturation.is_none() && self.brightness.is_none()
    }

    // same colour for the eye: two decimals
    pub fn same(&self, other: &Hsb) -> bool {
        let round = |v: Option<f64>| (v.unwrap_or(0.0) * 100.0).round();

        round(self.hue) == round(other.hue)
            && round(self.saturation) == round(other.saturation)
            && round(self.brightness) == round(other.brightness)
    }

    pub fn random() -> Hsb {
        let mut rng = rand::rng();

        Hsb {
            hue: Some(rng.random::<f64>()),
            saturation: Some(0.5 + rng.random::<f64>() * 0.5),
            brightness: None,
        }
    }

    // a web colour name, or #rgb / #rrggbb
    pub fn parse(spec: &str) -> Result<Hsb, ColorError> {
        let rgb = if let Some(hex) = spec.strip_prefix('#') {
            let digits: Vec<u32> = hex.chars().filter_map(|c| c.to_digit(16)).collect();

            match (hex.len(), digits.len()) {
                (6, 6) => [digits[0] * 16 + digits[1], digits[2] * 16 + digits[3], digits[4] * 16 + digits[5]],
                (3, 3) => [digits[0] * 17, digits[1] * 17, digits[2] * 17],
                _ => return Err(ColorError::Crash),
            }
        } else {
            let name = spec.to_lowercase();

            match NAMES.iter().find(|(n, _)| *n == name) {
                Some((_, rgb)) => [rgb[0] as u32, rgb[1] as u32, rgb[2] as u32],
                None => return Err(ColorError::Invalid),
            }
        };

        let (h, s, l) = rgb_to_hsl(rgb[0] as f64 / 255.0, rgb[1] as f64 / 255.0, rgb[2] as f64 / 255.0);

        // hsl to hsb
        let b = (2.0 * l + s * (1.0 - (2.0 * l - 1.0).abs())) / 2.0;

        if b == 0.0 {
            return Err(ColorError::Crash);
        }

        Ok(Hsb::new(h, 2.0 * (b - l) / b, b))
    }

    // integers for a device: hue 0..65535 for philips, 0..360 for nanoleaf / homekit
    pub fn scaled(&self, range: Range) -> [Option<i64>; 3] {
        let scale = |value: Option<f64>, max: f64| value.map(|v| (v * max) as i64);

        [
            scale(self.hue, range.hue),
            scale(self.saturation, range.saturation),
            scale(self.brightness, range.brightness),
        ]
    }
}

#[derive(Clone, Copy)]
pub struct Range {
    pub hue: f64,
    pub saturation: f64,
    pub brightness: f64,
}

pub const PHILIPS: Range = Range { hue: 65535.0, saturation: 254.0, brightness: 254.0 };
pub const HOMEKIT: Range = Range { hue: 360.0, saturation: 100.0, brightness: 100.0 };

fn rgb_to_hsl(r: f64, g: f64, b: f64) -> (f64, f64, f64) {
    let vmin = r.min(g).min(b);
    let vmax = r.max(g).max(b);
    let diff = vmax - vmin;
    let vsum = vmin + vmax;
    let l = vsum / 2.0;

    if diff < FLOAT_ERROR {
        return (0.0, 0.0, l);
    }

    let s = if l < 0.5 { diff / vsum } else { diff / (2.0 - vsum) };

    let dr = (((vmax - r) / 6.0) + (diff / 2.0)) / diff;
    let dg = (((vmax - g) / 6.0) + (diff / 2.0)) / diff;
    let db = (((vmax - b) / 6.0) + (diff / 2.0)) / diff;

    let mut h = if r == vmax {
        db - dg
    } else if g == vmax {
        (1.0 / 3.0) + dr - db
    } else {
        (2.0 / 3.0) + dg - dr
    };

    if h < 0.0 {
        h += 1.0;
    }
    if h > 1.0 {
        h -= 1.0;
    }

    (h, s, l)
}
