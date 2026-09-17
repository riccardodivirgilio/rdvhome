# LIGHTS — rdvhome app

Home-automation app in this repo (`github.com/riccardodivirgilio/rdvhome`, `master`). Runs on a
Raspberry Pi as `lights.service`, serving an HTTP API on `:8500` (`/switch`, `/switch/all/off`, …)
plus HomeKit (`hap-python`) and GPIO relays. Devices are defined in `run.py`.

## Deploy

    ./run.sh deploy      # rsync repo -> Pi, write systemd units, pip install, restart lights.service

Do **not** hand-edit on the Pi; edit here, commit, `./run.sh deploy`. Verify:
`curl -s http://lights.impazzito.it:8500/switch` → `200` (a hang/500 means it's blocking on an
unreachable device IP — check the domains resolve and the device is up).

## The Pi

hostname `rdvhome`, MAC `b8:27:eb:02:d4:4c`, **DHCP** (NetworkManager `auto`). On **IoT**
`10.10.5.10`, **`lights.impazzito.it`**. SSH `pi@lights.impazzito.it` (key auth). Runs from
`/home/pi/rdvhome`. Also **`rdvhome.local`** (mDNS): it still works from other VLANs because the
UXG reflects mDNS (see [[FIREWALL]]). The Raycast extension and the native app use it. It's on the
dumb switch on UXG port 2 (see [[LAN]]).

**iPhone + iCloud Private Relay:** Relay resolves `lights.impazzito.it` through public DNS → the
WAN wildcard `195.32.7.119`, where `:8500` isn't forwarded, so the page loads forever. Use
`http://rdvhome.local:8500` (Relay never handles `.local` names), or turn Relay off for the
`RdvHome` Wi-Fi (Settings → Wi-Fi → ⓘ → iCloud Private Relay).

## Devices (all IoT, fixed IP + local DNS, addressed by domain in run.py)

| Device        | app id         | MAC               | IP          | domain                    | token   |
| ------------- | -------------- | ----------------- | ----------- | ------------------------- | ------- |
| Philips Hue   | (philips)      | 00:17:88:76:cf:cf | 10.10.5.20  | philips.impazzito.it      | in run.py |
| Nanoleaf pc   | `nanoleaf_tv`  | 00:55:da:54:f7:3b | 10.10.5.31  | nanoleaf-pc.impazzito.it  | `lWI4…`   |
| Nanoleaf exa  | `nanoleaf_exa` | 80:8a:f7:05:f3:79 | 10.10.5.30  | nanoleaf-exa.impazzito.it | `XIp9…` (re-paired) |

- **ids vs names**: the internal ids (`nanoleaf_tv`, `nanoleaf_exa`) are unchanged — scenes/effects
  reference them. Only the **domains** carry the real names (pc/exa). `nanoleaf_tv` id = the **pc**.
- **Identify by behavior, not label**: setting a color proved `lWI4` = pc (it changed); the token
  is the ground truth, not the id name or OUI (the controller shows `00:55:da` as "IEEE
  Registration Authority" but it's Nanoleaf).
- exa is a **Shapes F379** (NL42) also in Apple Home; pc is an old NL22 Light Panels.
- Still stale in `run.py`: a Samsung TV `192.168.67.235` (`id=tv`) — needs a domain when wanted.

Reservations + local DNS are set via UniFi `rest/user` (`use_fixedip`, `fixed_ip`, `network_id`=IoT,
`local_dns_record`). Because these are Wi-Fi, moving them onto IoT needs a DHCP renew/kick.

## Nanoleaf local API

`http://<ip-or-domain>:16021/api/v1/<token>/…`. Read `.../state`; set colour with
`PUT .../state` body `{"on":{"value":true},"hue":{"value":0-360},"sat":{"value":0-100},"brightness":{"value":0-100}}`
(red=0, green=120, blue=240). `GET .../` returns name/model/serial — use it to confirm which token
maps to which panel.

**Minting a token** (needed after a factory reset / HomeKit re-setup — the old token then 401s):
1. Device must be on Wi-Fi and reachable (`:16021` answers, not `000`). If it was reset, re-add it
   to `RdvHome` Wi-Fi first (Nanoleaf/Home app) — UniFi may show it "online" (radio associated)
   while it's actually unreachable (ARP `PROBE`, stale `last_seen`); trust `:16021`, not the UI.
2. Enter pairing mode: hold the on/off button **~5-7s, only until the LED flashes** (holding ~15s
   factory-resets it and drops Wi-Fi).
3. Within ~30s: `POST http://<ip>:16021/api/v1/new` → `{"auth_token":"…"}`. A poll loop that
   fires `/new` every ~2s catches the window with no timing pressure.
4. Put the token in the device's `run.py` entry, `./run.sh deploy`.

## Mock servers (test the app without touching the live lights)

    docker compose up --build     # app on localhost:8500, talking only to the mocks
    python3 mock-test.py          # checks the mocks against the captures (localhost only)

`run.py` reads the device hosts from the environment, defaulting to the real ones:
`RDV_PHILIPS_GATEWAY_HOST`, `RDV_NANOLEAF_PC_HOST`, `RDV_NANOLEAF_EXA_HOST`. The compose `app`
service (stock `ghcr.io/astral-sh/uv` image, repo mounted, `uv run --with-requirements … python
run.py run`) sets them to `mock-philips` / `mock-nanoleaf`. From the host the mocks are on
`localhost:8580` (philips) and `localhost` (nanoleaf, port is always 16021), e.g.
`RDV_PHILIPS_GATEWAY_HOST=localhost:8580 RDV_NANOLEAF_PC_HOST=localhost RDV_NANOLEAF_EXA_HOST=localhost ./run.sh run`.

Two small Rust servers (`mock-philips`, `mock-nanoleaf`; only dep `serde_json`; same `src/main.rs`,
device logic in `src/device.rs`) that emulate the devices:

- **State in memory**, seeded from the captured GETs: a PUT changes it, the next GET reads it back
  (set blue → reads blue), until the container restarts. Responses reuse the captured headers.
- **Auth ignored**: any token works. A known nanoleaf token selects pc vs exa, unknown → exa.
- **Validation like the real devices** (each rule below was observed and is replayed byte for byte):
  - Hue: always `200` with a list, errors first then successes. `2` invalid json, `3` unknown
    light, `6` unknown parameter (or `hue` on the plug), `7` invalid value (description really is
    `invalid value, 70000}, for parameter, hue`), `201` "not modifiable. Device is set to off" for
    everything but `on`/`bri` while off (`{"on":true,"hue":…}` together works). `bri: 255` is
    clamped to 254, `{}` → `[]`, unreachable lights still answer success.
  - Nanoleaf: empty bodies. `204` ok, `422` invalid json, `404` unknown attribute/path, `400` wrong
    type/shape, value outside min..max, unknown effect (not in that device's `effectsList`) or
    unknown write command. A refused PUT changes nothing. `{}` gets a broken response with no
    status line (so does the mock). hue/sat/ct → `colorMode` hs/ct and `"*Solid*"`; an effect →
    `colorMode: effect`, on.
- Assumed, not observed: sat/ct clamping on Hue, integers-only on Nanoleaf, `*_inc` unsupported on
  the Hue mock. Anything not emulated falls back to the most similar static capture.

The captures are **not in git** (gitignored, mounted into the mocks as a volume): on a fresh clone run
`python3 mock-capture.py` and `python3 mock-capture.py --validation` once, otherwise the mocks start
empty. `mock-capture.py` (and `--validation`) recorded the raw request/response pairs in
`mock-*/captures/*.http`, with the same headers aiohttp sends, one request per second. It only does
GETs, refused requests and PUTs that write back the current value. **Careful**: the bridge accepts
`bri` on a light that is off, so the `bri: 255` probe really stores 254 (restore it afterwards).

Observed: Hue answers `200` + `[{"success":{…}}]` with `Connection: close` and no
`Content-Length`; Nanoleaf answers writes with an empty `204`, an unknown effect with an empty `400`.
