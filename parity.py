#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets"]
# ///
# Check that the rust app (rdvhome-rs, :8501) answers like the python app (:8500):
# same requests to both, bodies compared byte for byte. Each app has its own
# mocks, their final state is compared too. Never talks to the real lights.
#
# Usage: uv run parity.py [--keep]
#   starts from scratch (containers and data volumes are recreated) unless --keep
#   (--keep is for a quick look: the two apps may have drifted apart, and the
#   python app in docker loses its watch loops after a while, its fake gpio
#   reads a pin file while it is being written)
#
# Normalised before comparing: "unixtime", the order of "alias" (random in
# python), random colours of the scenes. Known differences are in KNOWN.

import asyncio
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

import websockets

PY, RS = "localhost:8500", "localhost:8501"
MOCKS = [("localhost:8580", "localhost:8581"), ("localhost:16021", "localhost:16022")]
SERVICES = ["app", "app-rs", "mock-philips", "mock-nanoleaf", "mock-philips-rs", "mock-nanoleaf-rs"]
failures = 0

# python answers 500 to anything sent to "all": philips_pool cannot be switched
# (NotImplementedError). The devices are switched anyway. Rust answers 200.
KNOWN = {"/switch/all/off": "python 500 (philips_pool)"}

# led_tv and led_living_room hang on the same relay. Python reports them on only when
# the mains AND the zigbee state say so, so the strip you did not touch stayed off
# until the next hue poll (and stayed off for good while the bridge was away), though
# it was lit in the room. Rust ORs the two instead, see powered.rs. Their "on" / "off"
# is blanked on both sides: everything else about those switches is still compared,
# but a real regression of that one field on those two would not be caught here.
POWERED = ("led_tv", "led_living_room")


def blank_powered(text):
    switch, out = None, []
    for line in text.splitlines(True):
        found = re.search(r'"id": "([a-z_]+)"', line)
        if found:
            switch = found.group(1)
        if switch in POWERED:
            line = re.sub(r'"(on|off)": (?:true|false)', r'"\1": "?"', line)
        out.append(line)
    return "".join(out)


def check(name, ok, detail=""):
    global failures
    failures += not ok
    print("ok  " if ok else "FAIL", name, "" if ok else "\n     " + detail)


def fetch(host, path, method="GET"):
    request = urllib.request.Request("http://%s%s" % (host, path), method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.headers.get("Content-Type"), response.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), e.read()


def normalise(body, colors=False):
    text = body.decode() if isinstance(body, bytes) else body
    text = re.sub(r'"unixtime": [0-9.e+-]+', '"unixtime": 0', text)
    text = blank_powered(text)
    text = re.sub(
        r'"alias": \[([^\]]*)\]',
        lambda m: '"alias": [%s]' % ", ".join(sorted(a.strip() for a in m.group(1).split(","))),
        text,
    )
    if colors == "round":
        text = re.sub(r'"(hue|saturation|brightness)": ([0-9.e+-]+)', lambda m: '"%s": %.2f' % (m.group(1), float(m.group(2))), text)
    elif colors:
        text = re.sub(r'"(hue|saturation|brightness)": [0-9.e+-]+', r'"\1": 0', text)
    return text


def first_difference(a, b):
    for n, (x, y) in enumerate(zip(a.splitlines(), b.splitlines())):
        if x != y:
            return "line %s: python %r, rust %r" % (n + 1, x, y)
    return "python %s lines, rust %s lines" % (len(a.splitlines()), len(b.splitlines()))


def same(path, method="GET", wait=0.0, colors=False):
    # not from scratch: the apps may have saved the same colour differently (what
    # was asked, 0.1, or what the bridge made of it, 0.09999)
    colors = colors or ("--keep" in sys.argv and "round")
    (ps, pt, pb), (rs, rt, rb) = fetch(PY, path, method), fetch(RS, path, method)
    name = "%s %s -> %s" % (method, path, ps)

    if path in KNOWN:
        print("skip", name, "known difference:", KNOWN[path])
    elif ps == 500 or method == "HEAD":
        # python answers with the django debug page
        check(name, ps == rs, "rust %s" % rs)
    elif pt and pt.startswith("text/plain"):
        a, b = normalise(pb, colors), normalise(rb, colors)
        check(name, (ps, pt) == (rs, rt) and a == b, "rust %s %s, %s" % (rs, rt, first_difference(a, b)))
    else:
        check(name, (ps, pt, pb) == (rs, rt, rb), "rust %s %s, %s bytes vs %s" % (rs, rt, len(pb), len(rb)))

    time.sleep(wait)


async def events(host, messages, listen):
    received = []
    async with websockets.connect("ws://%s/websocket" % host, max_size=None) as ws:
        for message in messages:
            await ws.send(message)
            try:
                while True:
                    received.append(await asyncio.wait_for(ws.recv(), listen))
            except asyncio.TimeoutError:
                pass
        await ws.send("/close")
    return received


def same_events(name, messages, listen=1.5, colors=False):
    async def both():
        return await asyncio.gather(events(PY, messages, listen), events(RS, messages, listen))

    # A poll of the hue bridge can land in the middle (both apps send a status
    # of the light then, python also when the poll crosses a command): compare
    # which events were seen, not how many times, and try again when they differ.
    random_colors, colors = colors, colors or ("--keep" in sys.argv and "round")

    def polled(event):
        # With random colours the bridge rounds what it is told (254 steps), so the
        # next poll often sees "another colour" and sends a status of the light: it
        # lands inside the listening window or not. Not what is compared here.
        event = json.loads(event)
        return random_colors and "name" in event and event["allow_hue"] and not event["effects"]

    for attempt in range(3):
        py, rs = (sorted(set(normalise(e, colors) for e in side if not polled(e))) for side in asyncio.run(both()))
        if py == rs:
            break
        time.sleep(4)
    detail = ""
    if py != rs:
        only_py = [e for e in py if e not in rs]
        only_rs = [e for e in rs if e not in py]
        detail = "%s/%s events; only python: %s\n     only rust: %s" % (
            len(py), len(rs),
            [json.loads(e) for e in only_py][:2],
            [json.loads(e) for e in only_rs][:2],
        )
    check("ws %s (%s events)" % (name, len(py)), py == rs, detail)


def fresh():
    compose = ["docker", "compose"]
    subprocess.run(compose + ["rm", "-sf"] + SERVICES, check=True, capture_output=True)
    subprocess.run(["docker", "volume", "rm", "-f", "rdvhome_app-data", "rdvhome_app-rs-data"], check=True, capture_output=True)
    subprocess.run(compose + ["up", "-d", "--build"] + SERVICES, check=True, capture_output=True)


def wait_for_apps():
    for host in (PY, RS):
        for _ in range(120):
            try:
                if fetch(host, "/switch/philips_pool")[0] == 200:
                    break
            except OSError:
                pass
            time.sleep(1)
        else:
            raise SystemExit("%s does not answer" % host)
    # the first poll of the hue bridge
    time.sleep(5)


def main():
    if "--keep" not in sys.argv:
        fresh()
    wait_for_apps()

    # status
    same("/switch")
    same("/switch/led_tv")
    same("/switch/default")
    same("/switch/nanoleaf")
    same("/switch/control")
    same("/switch/nope")
    same("/switch?number=led_tv")

    # relay + hue strip, and the strip that shares its relay
    same("/switch/led_tv/on", wait=1)
    same("/switch/led_tv")
    same("/switch/led_living_room")
    same("/switch/led_tv/-/50/60/70")
    same("/switch/led_tv/-/0/-/-")
    same("/switch/led_tv/color/red")
    same("/switch/led_tv/color/AliceBlue")
    same("/switch/led_tv/set?mode=on&color=%23ff8800")
    same("/switch/led_tv/set?color=green&hue=10")
    same("/switch/led_tv", wait=4)
    same("/switch/led_tv")
    same("/switch/led_tv/off", wait=1)
    same("/switch/led_living_room")

    # relay only, hue only
    same("/switch/spotlight_kitchen/on")
    same("/switch/spotlight_kitchen/color/red")
    same("/switch/spotlight_kitchen")
    same("/switch/led_kitchen/on/10/20/30")
    same("/switch/led_kitchen")
    same("/switch/lamp_hipster_room/off")

    # nanoleaf
    same("/switch/nanoleaf_tv/on")
    same("/switch/nanoleaf_tv/set?effect=Forest")
    same("/switch/nanoleaf_tv")
    same("/switch/nanoleaf/set?effect=Jungle")
    same("/switch/nanoleaf/color/blue")
    same("/switch/nanoleaf")
    same("/switch/nanoleaf_exa/off/10/10/10")
    same("/switch/nanoleaf_exa/stop")

    # windows, tv
    same("/switch/window_tv/up")
    same("/switch/window_tv")
    same("/switch/window_tv/down")
    same("/switch/window_tv/stop")
    same("/switch/window_kitchen/on")
    same("/switch/tv/on")
    same("/switch/tv/off")

    # aliases
    # the unreachable bulbs go back to off at the next poll
    same("/switch/default/on", wait=5)
    same("/switch/default")
    same("/switch/default/off", wait=1)
    same("/switch/all/off")

    # errors
    same("/switch/led_tv/color/nope")
    same("/switch/led_tv/color/black")
    same("/switch/led_tv/set?color=%23ff")
    same("/switch/led_tv/set?hue=abc")
    same("/switch/led_tv/set?hue=101")
    same("/switch/led_tv/set?hue=-1")
    same("/switch/led_tv/set?hue=")
    same("/switch/led_tv/set?mode=bogus")
    same("/switch/led_tv/set?mode=")
    same("/switch/led_tv/on/abc/1/1")
    same("/switch/led_tv/bogus")
    same("/switch/led%20tv")
    same("/switch/")
    same("/nope")
    same("/switch", method="POST")
    same("/nope", method="POST")
    same("/switch", method="HEAD")

    # homekit: every app has its own setup code
    for path, shape in (("/homekit", r'"paircode": "\d{3}-\d{2}-\d{3}",\s+"uri": "X-HM://[0-9A-Z]{13}",\s+"status": 200'), ("/qrcode", r"<svg ")):
        (ps, pt, pb), (rs, rt, rb) = fetch(PY, path), fetch(RS, path)
        check("GET %s -> %s" % (path, ps), (ps, pt) == (rs, rt) and all(re.search(shape, b.decode()) for b in (pb, rb)), "rust %s %s %s" % (rs, rt, rb[:200]))

    # frontend
    same("/")
    index = fetch(PY, "/")[2].decode()
    for asset in sorted(set(re.findall(r'(?:href|src)="?(/(?:css|js)/[^" >]+)', index))):
        same(asset)
    same("/css/nope.css")
    same("/css/")

    # websocket: the same events
    same_events("status", ["/switch"])
    same_events("light", ["/switch/led_tv/on", "/switch/led_tv/-/10/20/30", "/switch/led_tv/off"])
    same_events("nanoleaf", ["/switch/nanoleaf_tv/on", "/switch/nanoleaf/set?effect=Forest", "/switch/nanoleaf_tv/color/red"])
    same_events("window", ["/switch/window_tv/up", "/switch/window_tv/stop"])
    same_events("errors are silent", ["/switch/led_tv/set?hue=abc", "/nope", "/switch/nope/on"])
    same_events("scene", ["/switch/nanoleaf/on", "/switch/led_kitchen/on", "/switch/natural/on"], listen=2.5, colors=True)
    same_events("scene with random colours", ["/switch/random/on"], listen=2.5, colors=True)
    same_events("all off", ["/switch/default/off", "/switch/nanoleaf/off"], listen=2, colors=True)

    # the command line: same output (python prints its gpio debug lines first)
    python = ["docker", "compose", "exec", "-T", "app", "uv", "run", "-q", "--no-project", "--with-requirements", "rdvhome/requirements.txt", "python", "run.py"]
    rust = ["docker", "compose", "exec", "-T", "app-rs", "/rdvhome"]
    for arguments in (["on", "nanoleaf"], ["off", "nanoleaf"], ["on", "spotlight_kitchen", "led_tv"], ["off", "spotlight_kitchen", "led_tv"], ["on"], ["off", "default"], ["on", "nope"]):
        a, b = (
            [l for l in subprocess.run(cmd + arguments, capture_output=True, text=True).stdout.splitlines() if l.startswith(("on:", "off:"))]
            for cmd in (python, rust)
        )
        check("cli %s -> %s" % (" ".join(arguments), a), a == b and len(a) == 1, "rust %s" % b)
    time.sleep(4)

    # the scenes left random colours: paint everything the same
    for path in ("/switch/default/on", "/switch/default/-/10/20/30", "/switch/default/off"):
        same(path, wait=1)

    # what the devices were told: the two pairs of mocks are in the same state
    # (python can keep the colour it was told instead of what the bridge rounded it to)
    time.sleep(4)
    same("/switch", colors="round")
    tokens = re.findall(r'access_token = \'([^\']+)\'', open("run.py").read())
    paths = ["/api/x/lights/"] + ["/api/v1/%s/state" % t for t in tokens] + ["/api/v1/%s/effects/select" % t for t in tokens]
    for py_mock, rs_mock in MOCKS:
        for path in paths:
            if ("lights" in path) == py_mock.endswith("8580"):
                a, b = fetch(py_mock, path)[2], fetch(rs_mock, path)[2]
                check("mock %s%s" % (py_mock, path[:24]), a == b, first_difference(a.decode().replace(",", ",\n"), b.decode().replace(",", ",\n")))

    print("\n%s failures" % failures)
    raise SystemExit(failures and 1 or 0)


if __name__ == "__main__":
    main()
