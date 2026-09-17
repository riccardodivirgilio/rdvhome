#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["aiohomekit"]
# ///
# Is the rust HomeKit bridge a drop-in replacement of the python one (hap-python)?
# A real controller (aiohomekit, what Home Assistant uses) pairs with the python
# app, then the accessory.state of the python app is given to the rust app and
# the same pairing must keep working: same accessories, writes, events.
# Then the pairing is removed and a new one is made with the rust app alone.
#
# Usage: uv run homekit-test.py      (on the host, drives docker compose)
# Only the docker mocks are involved, never the real lights.

import asyncio
import json
import os
import subprocess
import sys
import urllib.request

WORK = "/work/.homekit-test"
ALIAS = "test"
failures = 0


def check(name, ok, detail=""):
    global failures
    failures += not ok
    print("ok  " if ok else "FAIL", name, "" if ok else "\n     %s" % (detail,), flush=True)


def get(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read())


def without_values(accessories):
    return [
        {**a, "services": [{**s, "characteristics": [{k: v for k, v in c.items() if k != "value"} for c in s["characteristics"]]} for s in a["services"]]}
        for a in accessories
    ]


# ---- inside the docker network ----


async def controller():
    from aiohomekit import Controller
    from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf

    zeroconf = AsyncZeroconf()
    browser = AsyncServiceBrowser(zeroconf.zeroconf, ["_hap._tcp.local.", "_hap._udp.local."], handlers=[lambda **kwargs: None])
    return Controller(async_zeroconf_instance=zeroconf), browser


async def pair(ctl, app):
    info = get("http://%s:8500/homekit" % app)
    for _ in range(30):
        async for discovery in ctl.async_discover():
            if not discovery.paired:
                print("found", discovery.description.name, discovery.description.id, flush=True)
                finish = await discovery.async_start_pairing(ALIAS)
                return await finish(info["paircode"])
        await asyncio.sleep(1)
    raise SystemExit("no unpaired accessory found for %s" % app)


async def exercise(pairing, app):
    accessories = await pairing.list_accessories_and_characteristics()
    check("%s: %s accessories" % (app, len(accessories)), len(accessories) == 42)

    # aid 3 is spotlight_kitchen (relay), iid 9 its On
    await pairing.put_characteristics([(3, 9, False)])
    await asyncio.sleep(1)

    events = []
    pairing.dispatcher_connect(events.append)
    await pairing.subscribe([(3, 9), (2, 10)])

    await pairing.put_characteristics([(3, 9, True)])
    await asyncio.sleep(1)
    check("%s: write On reaches the switch" % app, get("http://%s:8500/switch/spotlight_kitchen" % app)["switches"]["spotlight_kitchen"]["on"] is True)
    check("%s: read back" % app, (await pairing.get_characteristics([(3, 9)]))[(3, 9)]["value"] in (True, 1))

    get("http://%s:8500/switch/spotlight_kitchen/off" % app)
    await asyncio.sleep(2)
    check("%s: event when the switch changes" % app, any(e.get((3, 9), {}).get("value") in (False, 0) for e in events), events)

    # colour: aid 2 is led_kitchen, iid 10 its Hue
    await pairing.put_characteristics([(2, 9, True)])
    await asyncio.sleep(1)
    await pairing.put_characteristics([(2, 10, 120)])
    await asyncio.sleep(1)
    hue = get("http://%s:8500/switch/led_kitchen" % app)["switches"]["led_kitchen"]["hue"]
    check("%s: write Hue reaches the light" % app, abs(hue - 120 / 360) < 0.01, hue)

    pairings = await pairing.list_pairings()
    check("%s: list pairings" % app, len(pairings) == 1 and pairings[0]["controllerType"] == "admin", pairings)
    return accessories


async def inside(phase):
    os.makedirs(WORK, exist_ok=True)
    ctl, browser = await controller()
    data = os.path.join(WORK, "pairing.json")

    async with ctl:
        await asyncio.sleep(3)

        if phase == "python":
            pairing = await pair(ctl, "app")
            accessories = await exercise(pairing, "app")
            json.dump(accessories, open(os.path.join(WORK, "accessories.json"), "w"))
            json.dump({ALIAS: pairing.pairing_data}, open(data, "w"))

        elif phase == "dropin":
            ctl.load_data(data)
            pairing = ctl.aliases[ALIAS]
            # same id, new address: found again through mdns like an iPhone does
            accessories = await exercise(pairing, "app-rs")
            before = json.load(open(os.path.join(WORK, "accessories.json")))
            check("drop-in: same accessories as the python app", without_values(accessories) == without_values(before))
            config = pairing.description.config_num if pairing.description else None
            print("config number", config, flush=True)
            await pairing.remove_pairing(pairing.pairing_data["iOSPairingId"])
            check("drop-in: pairing removed", True)

        elif phase == "fresh":
            pairing = await pair(ctl, "app-rs")
            await exercise(pairing, "app-rs")
            await pairing.remove_pairing(pairing.pairing_data["iOSPairingId"])

    await browser.async_cancel()
    raise SystemExit(failures and 1 or 0)


# ---- on the host ----


def sh(*command, check_=True):
    print("$", " ".join(command), flush=True)
    return subprocess.run(command, check=check_)


def phase(name):
    return sh(
        "docker", "compose", "run", "--rm", "-T", "homekit-test", "uv", "run", "--script", "/work/homekit-test.py", "--inside", name,
        check_=False,
    ).returncode


def host():
    services = ["app", "app-rs", "mock-philips", "mock-nanoleaf", "mock-philips-rs", "mock-nanoleaf-rs"]
    sh("docker", "compose", "rm", "-sf", *services)
    sh("docker", "volume", "rm", "-f", "rdvhome_app-data", "rdvhome_app-rs-data")
    sh("rm", "-rf", ".homekit-test")

    # 1. a controller pairs with the python app
    sh("docker", "compose", "up", "-d", "--build", "app", "mock-philips", "mock-nanoleaf")
    if phase("python"):
        raise SystemExit("the controller could not pair with the python app")
    failed = 0

    # 2. the rust app takes over its state
    sh("docker", "compose", "cp", "app:/app/rdvhome/data/accessory.state", ".homekit-test/accessory.state")
    sh("docker", "compose", "stop", "app")
    sh("docker", "compose", "create", "--build", "app-rs")
    sh("docker", "compose", "cp", ".homekit-test/accessory.state", "app-rs:/data/accessory.state")
    sh("docker", "compose", "up", "-d", "app-rs")
    failed += phase("dropin")

    # 3. and can be paired from scratch
    failed += phase("fresh")

    sh("docker", "compose", "up", "-d", *services)
    print("\n%s" % ("FAILED" if failed else "homekit: all good"))
    raise SystemExit(failed and 1 or 0)


if __name__ == "__main__":
    if "--inside" in sys.argv:
        asyncio.run(inside(sys.argv[-1]))
    else:
        host()
