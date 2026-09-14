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
`/home/pi/rdvhome`. Was `rdvhome.local` (mDNS) — now on IoT, mDNS doesn't cross VLANs, so the app
and clients use the DNS name. It's on the dumb switch on UXG port 2 (see [[LAN]]).

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
