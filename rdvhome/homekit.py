# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import logging

from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from rpy.functions.functional import iterate

from rdvhome.switches import switches
from rdvhome.utils.gpio import get_gpio
from rdvhome.utils.persistence import data_path

"""An example of how to setup and start an Accessory.
This is:
1. Create the Accessory object you want.
2. Add it to an AccessoryDriver, which will advertise it on the local network,
    setup a server to answer client queries, etc.
"""

logging.basicConfig(level=logging.INFO)


def get_bridge(driver):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, get_gpio().is_debug and "RdvTest" or "RdvHome")

    for switch in switches:
        # bridge.add_accessory(LightBulb(driver, switch.name))
        for accessory in iterate(switch.create_homekit_accessory(driver) or ()):
            bridge.add_accessory(accessory)

    return bridge


# Start the accessory on port 51826
driver = AccessoryDriver(
    port=51826,
    loop=asyncio.get_event_loop(),
    persist_file=data_path("accessory.state"),
    # pincode = b"000-00-000"
)

# Change `get_accessory` to `get_bridge` if you want to run a Bridge.
driver.add_accessory(accessory=get_bridge(driver))
