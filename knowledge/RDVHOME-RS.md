# RDVHOME-RS — plan for the Rust rewrite

> **Status: plan, nothing built yet** (2026-09-17). Findings come from reading the Python app and
> from running it in `docker compose` against the mock servers (see [[LIGHTS]], "Mock servers").
> The real lights were never touched.

Goal: a new folder `rdvhome-rs/` with a Rust app that is a drop-in replacement for the Python app:
same HTTP request/response, same WebSocket protocol, same CLI. Built like `mock-philips` and like
`~/Wolfram/git/geoip-server/geocode-ip-rust` (static musl binary, `FROM scratch`). Compose runs the
old app, the mocks and the new app side by side, and a parity script proves they answer the same.

What is **not** copied: the class design. The outside is identical, the inside is redone (see
"New design").

## What the Python app does (the contract)

### HTTP

Every route is registered twice: `GET`, and a fake method `WS` used by the websocket (below).

| Route | Does |
|---|---|
| `/` , `/css/*`, `/js/*` | static frontend from `rdvhome/frontend/dist` |
| `/switch` | status of all switches |
| `/switch/{number}` | status, `number` = id **or alias** (`[a-zA-Z-0-9_-]+`) |
| `/switch/{number}/set?mode=&hue=&saturation=&brightness=&color=&effect=` | switch |
| `/switch/{number}/color/{color:[a-zA-Z-0-9]+}` | switch to a named colour |
| `/switch/{number}/{mode}` | mode = `-`, `on`, `off`, `up`, `down`, `stop` |
| `/switch/{number}/{mode}/{hue}/{saturation}/{brightness}` | each `-` or digits, 0..100 |
| `/homekit` | `{"paircode", "uri"}` |
| `/qrcode` | SVG of the HomeKit uri |
| `/websocket` | see below |

Arguments are `dict(query, **match_info)`: the path wins over the query string.

Response envelope, always `Content-Type: text/plain; charset=utf-8`:

```json
{
    "mode": "status",
    "switches": {"<id>": {...}},
    "status": 200,
    "success": true,
    "unixtime": 1789675050.15909
}
```

- JSON is `indent=4`, **ASCII escaped** (`"🍽"` for the icons), keys in insertion order.
- No switch matches: `"switches": {}`, `"status": 404`, HTTP 404.
- Errors: `{"reason": ..., "status", "success": false, "unixtime"}`. Reasons seen: `NotAnInteger`,
  `NotInRange`, `InvalidColor`, `InvalidMode` (400), `Not Found` (404, also when a path regex does
  not match, e.g. `/switch/x/on/abc/1/1`).
- `HEAD` / `POST` answer **500** (aiohttp's 405 falls in the generic `except`). With `DEBUG` it is a
  Django HTML error page, in production the JSON envelope with 500.
- Colours: `color` goes through the `colour` library (web names; `ff0000` without `#` is
  `InvalidColor`, and `#` cannot be in the path). hue/saturation/brightness are `int / 100`.

A full switch (status, and some events):

```
id, name, kind, icon, alias[], ordering, zone, room,
allow_on, allow_hue, allow_saturation, allow_brightness, allow_direction, allow_visibility,
effects{}, then state: on, off, hue, brightness, saturation, effect, up, down, intensity
```

A partial one (`full=False`) is `id` + the state that changed.

### WebSocket

- Client sends a **path as text** (`/switch`, `/switch/<id>/set?mode=on&hue=-&...`). The server
  routes it through the same router with method `WS` and **throws the response away**. Errors and
  404 are silent. `/close` closes.
- The server pushes **every event of every switch** to every socket, as the same indented JSON, one
  switch per message (not the envelope). The frontend sends `/switch` on connect and every 5 s of
  silence, and gets one message per switch.
- Who sends what (recorded on the mocks):

| Action | Event |
|---|---|
| status of anything | full |
| `Light.switch` | **partial** `{"id","on","off"}` / `{"id","hue","saturation"}` |
| `Nanoleaf.switch` on/colour | full + state + `"effect": null` |
| `Nanoleaf.switch` effect | full + `on: true` + `"effect": "Forest"` |
| Nanoleaf effect it does not have | full, no state |
| `Window.switch` | full + `up`, `down` |
| `ControlSwitch.switch` | full + `on`/`off`, plus one event per other scene switched off |
| Hue poller sees a change | full + state of that light |

### CLI

`./run.sh <command>`, no command prints the list: `deploy fab off on pair refactor run sun test_gpio`.

- `run [--open]`: server on `0.0.0.0:8500` + HomeKit on `51826`.
- `on [alias…]` (default `default`) prints `on: <sorted ids>`; `off [alias…]` (default `all`) prints
  `off: <sorted ids>`. They call the devices directly, no running server needed.
- `pair` prints the HomeKit setup message. `test_gpio` pulses the relays of `RELAY2`.
- `deploy` rsyncs to the Pi and writes the systemd units. `fab`, `refactor`, `sun` are dev leftovers
  (`sun.py` is not even a command, it runs at import).

### Devices and background loops

- **Light**: relay lights (gpio only), hue lights (philips only), and both (`led_living_room`,
  `led_tv`, `led_bedroom`). Relay = 25 ms low pulse on `gpio_relay` (a toggle!), power is read back
  from `gpio_status` (`on = not pin`). Watch loop polls the pin every 0.3 s.
- **PhilipsPoolControl**: invisible switch `philips_pool`, polls `GET /lights/` every 3 s, writes
  each light's state to `remote-<id>.json`, emits an event when on / allow_on / colour changed.
  A reachable light on the bridge's power-on colour (`hue .128, sat .551`) gets its saved colour
  pushed back.
- **Nanoleaf**: `GET /state` + `GET /effects/select` per status, no polling.
- **Window**: two gpio outputs (power, direction), auto stop after 13 s up / 12 s down (4 s in DEBUG),
  all outputs high at start.
- **TV**: polls `http://<ip>:8001/api/v2/` every 15 s, off = `KEY_POWER` over the Samsung websocket.
- **ControlSwitch** (scenes): in-memory `on`; turning one on turns the others off, optionally turns
  on `automatic_on` aliases, then colours every `allow_hue` switch that is on (fixed colour, list,
  perturbation function, or random), repeating on a random timeout, or once and off after 0.5 s.
- **Persistence**: `~/.rdvhome/` (`rdvhome/data/` in DEBUG): `remote-<id>.json`, `gpio-<n>.json`
  (fake gpio, DEBUG only), `accessory.state` (HomeKit keys and pairings).
- `DEBUG` = "RPi.GPIO cannot be imported".

### Quirks found (decide per item: copy, or fix and list as known difference)

1. `alias` is a `frozenset`: the order changes at every start. Rust: fixed order, parity compares as a set.
2. `unixtime` is `utcnow().timestamp()`: naive UTC read as local time, so on the Pi (Europe/Rome) it
   is 1–2 h behind. Nobody reads it (frontend uses its own clock, Swift only decodes it). **Fix**.
3. A zero colour component is the integer `0`, not `0.0` (`getattr(...) or 0`): `/color/red` gives
   `"hue": 0`. Copy (cheap) so bodies stay byte identical.
4. `@debounce(1)` resets `self._t = None` on every call, so **it never debounces**. Relay pulses and
   nanoleaf status are not rate limited today. Copy the behaviour (= no debounce), do not port the decorator.
5. `led_tv` and `led_living_room` share relay 20 / status 4: switching one off cuts both, and the
   other reports itself ~0.3 s later through its watch loop. The new design must make this explicit.
6. Nanoleaf `switch()` with nothing to do: `payload={}` is falsy, so it does a **GET /state** instead
   of a PUT (lucky: a `{}` PUT gets the broken response, see [[LIGHTS]]).
7. `Light.switch` always sends the zigbee command too, even right after cutting the power.
8. TV: `switch(on=None)` (a colour request to alias `all`) sets `self.on = None`. Fix: ignore.
9. `Light.switch` ignores `direction`, `Window.switch` ignores `on`: `/switch/all/off` does not stop windows.
10. Python `int()` accepts `" 5"`, `"+5"`, `"1_0"` in the query string. Rust: plain digits, known difference.
11. Python float `repr` vs Rust: same shortest round-trip digits, but exponents differ
    (`1e-05` vs `1e-5`). Needs a small formatter, values here are 0..1 so it is rare.

## New design (the part that must be better)

The Python `Light` is one class that is a relay, a status pin, a hue bulb, a json cache and the
merge rule between them, and `PhilipsPoolControl` reaches into it from outside. Replace inheritance
with **small devices and one combinator**:

```rust
trait Device {                       // one physical thing, knows nothing about the others
    async fn read(&self) -> State;               // State { on, allow_on, color, effect, up, down }
    async fn apply(&self, cmd: &Command) -> State;   // Command { on, color, effect, direction }
    fn changes(&self) -> broadcast::Receiver<State>; // its own watch loop feeds this
    fn capabilities(&self) -> Capabilities;
}
```

| Device | Is |
|---|---|
| `Relay { pulse_pin, status_pin }` | the physical switch: mains power, toggle by pulse, truth = status pin. `Arc`-shared, so relay 20 is **one** object used by two lights (quirk 5) |
| `HueLight { bridge, id }` | the zigbee bulb. State comes from the bridge poller, cached in `remote-<id>.json` |
| `HueBridge` | owns the 3 s poll and the HTTP client, feeds its `HueLight`s. Still listed as the invisible `philips_pool` entry for parity |
| `Nanoleaf`, `Tv`, `Window`, `Scene` | as today |
| `Gpio` trait | `RealGpio` (rppal, Linux + `/dev/gpiomem`) / `FileGpio` (today's `gpio-<n>.json`) |

The combinator is where and / or lives, in one place:

```rust
struct Powered<P: Device, L: Device> { power: P, light: L }   // relay + hue strip

read:   on       = power.on AND light.on        // what the user sees
        allow_on = light.allow_on OR true       // a relay can always be switched
        color    = light.color
apply:  on=true  -> power on (only if not powered), then light on
        on=false -> power off (only if powered), light off
        color    -> light only
changes: merge of both streams, re-evaluated through read()
```

`Switch` = metadata (id, name, alias, icon, zone, room, ordering) + a `Box<dyn Device>` + the event
fan-out. Serialisation, alias filtering and the websocket know only `Switch`. A relay-only spotlight
is `Switch(Relay)`, a bulb is `Switch(HueLight)`, a strip is `Switch(Powered(Relay, HueLight))`.

Configuration stays code, like `run.py`: `rdvhome-rs/src/home.rs` with builder functions
(`light()`, `window()`, `scene()`). The scene colour lambdas become an enum:
`Colors::{Random, Fixed(hsb), Cycle(vec), Perturb{base, factor}}`, `Timeout::Range(min, max)`.
Hosts come from the same `RDV_*_HOST` variables, plus `RDV_DATA_DIR`.

## Crates

- `tokio`, `axum` (router + websocket; unlike geoip this is not a two-route hot path), `serde_json`
  with `preserve_order` and a custom formatter (indent 4, ASCII escape, quirks 3 and 11).
- `reqwest` without TLS for Hue/Nanoleaf (Hue answers `Connection: close` without `Content-Length`),
  `tokio-tungstenite` for the TV, `rppal` for gpio (Linux only, behind `cfg`), `clap` for the CLI.
- Frontend `dist/` embedded in the binary (`include_dir`): scratch image and the Pi need one file.
- HomeKit: `hap` (hap-rs). **Biggest risk**, see below.

## Docker and compose

`rdvhome-rs/Dockerfile`: `rust:1-alpine` build → `FROM scratch`, same as the mocks; the frontend
comes in through compose `additional_contexts`. Compose gets:

- `app-rs` on `8501`, same env as `app`;
- a **second pair of mocks** for it (same images). Shared mocks would let one app's poller see the
  other app's writes and make parity depend on timing.

`parity.py` (like geoip's `scripts/parity.sh`, in python like `mock-test.py`): wipe both data dirs,
send the same sequence to `:8500` and `:8501` over HTTP and over the websocket, compare bodies byte
for byte after normalising `unixtime`, `alias` order, and random colours (scenes compared by shape).
Then compare the final state of the two mock pairs. CLI: run `on`/`off`/no-command in both, diff stdout.

## Phases

1. Skeleton: crate, Dockerfile, compose, `home.rs`, serialiser. `/switch` of a static list is byte identical.
2. Devices against the mocks: `FileGpio`, `Relay`, `HueBridge`/`HueLight`, `Powered`, `Nanoleaf`.
3. Routes, validation and errors; websocket; `parity.py` green for HTTP + WS.
4. `Window`, `Tv`, `Scene`. CLI `run`/`on`/`off`/`test_gpio`.
5. HomeKit + `pair`, `/homekit`, `/qrcode`.
6. Pi: cross build, `RealGpio`, new `deploy` (copy one binary + systemd unit). Only with the user there.

## Open questions

- **HomeKit pairing.** `accessory.state` is hap-python's format. hap-rs stores the same things
  (ed25519 keys, paired clients) differently; converting it and keeping the same accessory ids is
  possible but unproven. Fallback: pair the bridge again in the Home app (rooms and automations of
  ~25 accessories are lost). To decide before phase 5.
- **Pi architecture.** MAC `b8:27:eb` = Pi 1–3, so armv6/armv7/aarch64 depending on model and OS.
  Check `uname -m` before phase 6; it picks the musl target.
- `fab`, `refactor`, `sun`: proposed **not** ported. `deploy` ported with a different body.
- HEAD/POST → 500: proposed to keep the status (JSON envelope), never the Django page.
