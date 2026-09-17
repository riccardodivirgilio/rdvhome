#!/usr/bin/env python3
# Check the mock servers (docker compose up --build) against the captures:
# every captured "invalid" request must get the same bytes back that the real
# device sent (ignoring the Date header), then a few read-after-write scenarios.
#
# Usage: python3 mock-test.py   (talks only to localhost, never to the real lights)

import glob
import importlib.util
import json
import os
import re
import socket

ROOT = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("capture", os.path.join(ROOT, "mock-capture.py"))
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)

MOCKS = {"mock-philips": 8580, "mock-nanoleaf": 16021}
failures = 0


def send(port, request):
    with socket.create_connection(("localhost", port), timeout=5) as sock:
        sock.sendall(request)
        return capture.read_response(sock)


def check(name, ok, detail=""):
    global failures
    failures += not ok
    print("ok  " if ok else "FAIL", name, "" if ok else detail)


def call(port, method, path, payload=None):
    response = send(port, capture.build_request(method, "localhost", port, path, payload))
    head, _, body = response.partition(b"\r\n\r\n")
    return int(head.split(b" ")[1]), json.loads(body) if body.strip() else None


def strip_date(raw):
    return re.sub(rb"Date: [^\r]*\r\n", b"", raw)


for folder, port in MOCKS.items():
    for path in sorted(glob.glob(os.path.join(ROOT, folder, "captures", "*invalid*.http"))):
        name = os.path.basename(path)
        if name in ("exa-invalid-token.http", "exa-get-state-after-invalid.http"):
            continue  # auth is ignored on purpose / not a request with bad input
        request, expected = open(path, "rb").read().split(capture.SEPARATOR)
        if b"light-off" in name.encode():
            # these were captured on a light that was off
            light = request.split(b"/lights/")[1].split(b"/")[0].decode()
            call(port, "PUT", "/api/x/lights/%s/state" % light, {"on": False})
        got = send(port, request)
        check("%s/%s" % (folder, name), strip_date(got) == strip_date(expected), got.partition(b"\r\n\r\n")[2][:200])

# philips: blue stays blue
port = MOCKS["mock-philips"]
status, body = call(port, "PUT", "/api/x/lights/1/state", {"on": True, "hue": 46920, "sat": 254, "bri": 200})
check("philips put blue", status == 200 and all("success" in item for item in body), body)
state = call(port, "GET", "/api/x/lights/")[1]["1"]["state"]
check("philips reads blue", (state["on"], state["hue"], state["sat"], state["bri"]) == (True, 46920, 254, 200), state)
call(port, "PUT", "/api/x/lights/1/state", {"on": False})
status, body = call(port, "PUT", "/api/x/lights/1/state", {"hue": 1})
check("philips off refuses hue (201)", body[0]["error"]["type"] == 201, body)
check("philips off kept blue", call(port, "GET", "/api/x/lights/1")[1]["state"]["hue"] == 46920)

# nanoleaf: blue stays blue, per device
port = MOCKS["mock-nanoleaf"]
pc, exa = ("/api/v1/%s" % capture.NANOLEAF[name][2] for name in ("pc", "exa"))
blue = {"on": {"value": True}, "hue": {"value": 240}, "sat": {"value": 100}, "brightness": {"value": 80}}
check("nanoleaf put blue", call(port, "PUT", pc + "/state", blue)[0] == 204)
state = call(port, "GET", pc + "/state")[1]
check(
    "nanoleaf reads blue",
    [state[k]["value"] for k in ("on", "hue", "sat", "brightness")] == [True, 240, 100, 80] and state["colorMode"] == "hs",
    state,
)
check("nanoleaf colour means solid", call(port, "GET", pc + "/effects/select")[1] == "*Solid*")
check("nanoleaf other device untouched", call(port, "GET", exa + "/state")[1]["hue"]["value"] != 240)
check("nanoleaf refused put changes nothing", call(port, "PUT", pc + "/state", {"on": {"value": False}, "hue": {"value": 999}})[0] == 400
      and call(port, "GET", pc + "/state")[1]["on"]["value"] is True)
check("nanoleaf select effect", call(port, "PUT", pc + "/effects", {"select": "Forest"})[0] == 204)
check("nanoleaf reads effect", call(port, "GET", pc + "/effects/select")[1] == "Forest"
      and call(port, "GET", pc + "/state")[1]["colorMode"] == "effect")
check("nanoleaf effect of the other device", call(port, "PUT", pc + "/effects", {"select": "Jungle"})[0] == 400)
check("nanoleaf off", call(port, "PUT", pc + "/state", {"on": {"value": False}})[0] == 204
      and call(port, "GET", pc)[1]["state"]["on"]["value"] is False)

print("\n%s failures" % failures)
raise SystemExit(failures and 1 or 0)
