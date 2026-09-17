#!/usr/bin/env python3
# Capture raw HTTP request/response pairs from the real Philips Hue bridge and
# Nanoleaf panels, mimicking the requests rdvhome does through aiohttp.
#
# SAFE ON LIVE LIGHTS: only GETs, plus PUTs that write back the value that was
# just read (so nothing visibly changes). One request per second.
#
# Usage: python3 mock-capture.py [--validation]   (writes mock-*/captures/*.http)

import json
import os
import socket
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SEPARATOR = b"\n\n======== RESPONSE ========\n\n"

PHILIPS = ("philips.impazzito.it", 80, "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W")
NANOLEAF = {
    "pc": ("nanoleaf-pc.impazzito.it", 16021, "lWI4Ymlb9WkrELgfnXZBlQyeuXljzaw1"),
    "exa": ("nanoleaf-exa.impazzito.it", 16021, "XIp9FxkONwwxGs0jqWGeNrrhOIB76Rtb"),
}


def build_request(method, host, port, path, payload=None):
    # same headers, in the same order, as aiohttp 3.8 (see rdvhome/switches/philips.py)
    lines = [
        "%s %s HTTP/1.1" % (method, path),
        "Host: %s" % (host if port == 80 else "%s:%s" % (host, port)),
        "Accept: */*",
        "Accept-Encoding: gzip, deflate",
        "User-Agent: Python/3.11 aiohttp/3.8.3",
    ]
    body = b""
    if payload is not None:
        # bytes are sent as they are (to probe invalid json)
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        lines += ["Content-Length: %s" % len(body), "Content-Type: application/json"]
    return "\r\n".join(lines).encode() + b"\r\n\r\n" + body


def read_response(sock):
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = sock.recv(65536)
        if not chunk:
            return raw
        raw += chunk

    head, _, body = raw.partition(b"\r\n\r\n")
    headers = {
        k.strip().lower(): v.strip()
        for k, v in (l.split(b":", 1) for l in head.split(b"\r\n")[1:] if b":" in l)
    }
    status = int(head.split(b" ", 2)[1])

    def more():
        chunk = sock.recv(65536)
        if not chunk:
            raise EOFError
        return chunk

    try:
        if status in (204, 304):
            pass
        elif b"content-length" in headers:
            while len(body) < int(headers[b"content-length"]):
                body += more()
        elif headers.get(b"transfer-encoding", b"").lower() == b"chunked":
            while not body.endswith(b"0\r\n\r\n"):
                body += more()
        else:
            while True:
                body += more()
    except (EOFError, socket.timeout):
        pass

    return head + b"\r\n\r\n" + body


def capture(folder, name, method, host, port, path, payload=None):
    request = build_request(method, host, port, path, payload)

    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(request)
        response = read_response(sock)

    target = os.path.join(ROOT, folder, "captures", "%s.http" % name)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        f.write(request + SEPARATOR + response)

    print(name, "->", response.split(b"\r\n", 1)[0].decode(), "(%s bytes)" % len(response))
    time.sleep(1)

    return response.partition(b"\r\n\r\n")[2]


def main():
    host, port, token = PHILIPS
    base = "/api/%s/lights/" % token

    lights = json.loads(capture("mock-philips", "get-lights", "GET", host, port, base))
    light_id, light = sorted(lights.items())[0]
    # write back the current value: no visible change
    capture(
        "mock-philips", "put-light-state-on", "PUT", host, port,
        "%s%s/state" % (base, light_id), {"on": light["state"]["on"]},
    )

    for name, (host, port, token) in NANOLEAF.items():
        base = "/api/v1/%s" % token

        state = json.loads(capture("mock-nanoleaf", "%s-get-state" % name, "GET", host, port, base + "/state"))
        effect = json.loads(capture("mock-nanoleaf", "%s-get-effects-select" % name, "GET", host, port, base + "/effects/select"))
        # not used by the app: the mock needs it to tell a valid effect from an unknown one
        capture("mock-nanoleaf", "%s-get-effects-list" % name, "GET", host, port, base + "/effects/effectsList")
        if not effect.startswith("*"):
            # select again the effect that is already running (not *Solid* / *Dynamic*)
            capture(
                "mock-nanoleaf", "%s-put-effects-select-current" % name, "PUT", host, port,
                base + "/effects", {"select": effect},
            )
        # write back the current value: no visible change
        capture(
            "mock-nanoleaf", "%s-put-state-on" % name, "PUT", host, port,
            base + "/state", {"on": {"value": state["on"]["value"]}},
        )

    # unknown effect: the device refuses it, nothing changes
    host, port, token = NANOLEAF["pc"]
    capture(
        "mock-nanoleaf", "pc-put-effects-select-unknown", "PUT", host, port,
        "/api/v1/%s/effects" % token, {"select": "rdvhome-mock-does-not-exist"},
    )


def validation():
    # How the devices answer to bad input. Everything here is either refused or
    # writes back a value that is already set, so again nothing visibly changes.
    host, port, token = PHILIPS
    base = "/api/%s/lights/" % token

    lights = json.loads(capture("mock-philips", "get-lights", "GET", host, port, base))
    off = [k for k, v in sorted(lights.items()) if v["state"]["reachable"] and not v["state"]["on"] and "hue" in v["state"]]
    unreachable = [k for k, v in sorted(lights.items()) if not v["state"]["reachable"]]
    plugs = [k for k, v in sorted(lights.items()) if "hue" not in v["state"]]

    def philips(name, light_id, payload):
        capture("mock-philips", "invalid-%s" % name, "PUT", host, port, "%s%s/state" % (base, light_id), payload)

    philips("json", 1, b"{not json")
    philips("empty-object", 1, {})
    philips("unknown-parameter", 1, {"foo": 1})
    philips("hue-out-of-range", 1, {"hue": 70000})
    philips("on-wrong-type", 1, {"on": "yes"})
    philips("partial", 1, {"on": lights["1"]["state"]["on"], "hue": 70000})
    philips("unknown-light", 99, {"on": True})
    if off:
        # the bridge clamps and stores it even if the light is off: put the old value back
        philips("bri-out-of-range-light-off", off[0], {"bri": 255})
        capture(
            "mock-philips", "put-light-state-bri-light-off", "PUT", host, port,
            "%s%s/state" % (base, off[0]), {"bri": lights[off[0]]["state"]["bri"]},
        )
        philips("hue-same-value-light-off", off[0], {"hue": lights[off[0]]["state"]["hue"]})
    if unreachable:
        philips("on-same-value-unreachable", unreachable[0], {"on": lights[unreachable[0]]["state"]["on"]})
    if plugs:
        philips("hue-on-plug", plugs[0], {"hue": 100})

    host, port, token = NANOLEAF["exa"]
    base = "/api/v1/%s" % token

    def nanoleaf(name, path, payload):
        capture("mock-nanoleaf", "exa-invalid-%s" % name, "PUT", host, port, base + path, payload)

    capture("mock-nanoleaf", "exa-get-all", "GET", host, port, base)
    capture("mock-nanoleaf", "exa-invalid-token", "GET", host, port, "/api/v1/rdvhomeInvalidToken/state")
    capture("mock-nanoleaf", "exa-invalid-path", "GET", host, port, base + "/nope")
    nanoleaf("json", "/state", b"{not json")
    nanoleaf("empty-object", "/state", {})
    nanoleaf("unknown-parameter", "/state", {"foo": {"value": 1}})
    nanoleaf("on-wrong-type", "/state", {"on": {"value": "yes"}})
    nanoleaf("on-wrong-shape", "/state", {"on": True})
    nanoleaf("hue-wrong-type", "/state", {"hue": {"value": "blue"}})
    nanoleaf("effects-select-wrong-type", "/effects", {"select": 5})
    nanoleaf("effects-empty-object", "/effects", {})
    nanoleaf("effects-write-unknown-command", "/effects", {"write": {"command": "bogus"}})

    # out of range: brightness is already at max, so a clamp changes nothing
    before = json.loads(capture("mock-nanoleaf", "exa-get-state", "GET", host, port, base + "/state"))
    if before["brightness"]["value"] == before["brightness"]["max"]:
        nanoleaf("brightness-out-of-range", "/state", {"brightness": {"value": before["brightness"]["max"] + 1}})
        after = json.loads(capture("mock-nanoleaf", "exa-get-state-after-invalid", "GET", host, port, base + "/state"))
        if not after["on"]["value"] == before["on"]["value"]:
            print("!! brightness switched it on, restoring")
            capture("mock-nanoleaf", "exa-put-state-restore", "PUT", host, port, base + "/state", {"on": before["on"]})


if __name__ == "__main__":
    import sys

    validation() if "--validation" in sys.argv else main()
