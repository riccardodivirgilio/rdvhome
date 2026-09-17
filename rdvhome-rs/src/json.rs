// JSON written the way python's json.dumps(indent=4) does, so bodies are byte
// identical to the old app: 4 spaces, non ascii as \uXXXX, floats as repr().

use std::io::{self, Write};

use serde::Serialize;
use serde_json::ser::{Formatter, PrettyFormatter};

pub struct PythonFormatter<'a>(PrettyFormatter<'a>);

impl PythonFormatter<'_> {
    pub fn new() -> Self {
        PythonFormatter(PrettyFormatter::with_indent(b"    "))
    }
}

// repr(float): shortest digits that round-trip, exponent when < 1e-4 or >= 1e16
pub fn float_repr(value: f64) -> String {
    if !value.is_finite() {
        return "null".to_string();
    }

    // "1.2345e-5": rust gives the same shortest digits as python
    let scientific = format!("{:e}", value);
    let (mantissa, exponent) = scientific.split_once('e').unwrap();
    let exponent: i32 = exponent.parse().unwrap();

    if (-4..16).contains(&exponent) {
        let text = format!("{}", value);
        return if text.contains('.') { text } else { text + ".0" };
    }

    format!("{}e{}{:02}", mantissa, if exponent < 0 { '-' } else { '+' }, exponent.abs())
}

impl Formatter for PythonFormatter<'_> {
    fn write_f64<W: ?Sized + Write>(&mut self, writer: &mut W, value: f64) -> io::Result<()> {
        writer.write_all(float_repr(value).as_bytes())
    }

    fn write_string_fragment<W: ?Sized + Write>(&mut self, writer: &mut W, fragment: &str) -> io::Result<()> {
        for c in fragment.chars() {
            if c.is_ascii() {
                writer.write_all(&[c as u8])?;
            } else {
                for unit in c.encode_utf16(&mut [0; 2]) {
                    write!(writer, "\\u{:04x}", unit)?;
                }
            }
        }
        Ok(())
    }

    fn begin_array<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.begin_array(w)
    }

    fn end_array<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.end_array(w)
    }

    fn begin_array_value<W: ?Sized + Write>(&mut self, w: &mut W, first: bool) -> io::Result<()> {
        self.0.begin_array_value(w, first)
    }

    fn end_array_value<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.end_array_value(w)
    }

    fn begin_object<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.begin_object(w)
    }

    fn end_object<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.end_object(w)
    }

    fn begin_object_key<W: ?Sized + Write>(&mut self, w: &mut W, first: bool) -> io::Result<()> {
        self.0.begin_object_key(w, first)
    }

    fn begin_object_value<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.begin_object_value(w)
    }

    fn end_object_value<W: ?Sized + Write>(&mut self, w: &mut W) -> io::Result<()> {
        self.0.end_object_value(w)
    }
}

pub fn dumps<T: Serialize>(value: &T) -> String {
    let mut out = Vec::new();
    let mut serializer = serde_json::Serializer::with_formatter(&mut out, PythonFormatter::new());
    value.serialize(&mut serializer).expect("json");
    String::from_utf8(out).expect("utf8")
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn floats() {
        assert_eq!(float_repr(1.0), "1.0");
        assert_eq!(float_repr(0.49999237048905165), "0.49999237048905165");
        assert_eq!(float_repr(0.00001), "1e-05");
        assert_eq!(float_repr(0.0001), "0.0001");
        assert_eq!(float_repr(1.5e16), "1.5e+16");
        assert_eq!(float_repr(1789675050.15909), "1789675050.15909");
    }

    #[test]
    fn python_layout() {
        assert_eq!(
            dumps(&json!({"icon": "🍽", "alias": [], "effects": {}, "n": [1, 0.0]})),
            "{\n    \"icon\": \"\\ud83c\\udf7d\",\n    \"alias\": [],\n    \"effects\": {},\n    \"n\": [\n        1,\n        0.0\n    ]\n}"
        );
    }
}
