# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line
from rdvhome.utils.gpio import GPIO

import random
import uuid
import subprocess

RELAY1 = [22, 27, 17,  4,  3,  2]

RELAY2 = [16, 12,  7,  8, 25, 24]

INPUT  = [21, 20, 23, 18, 26, 19,
          13,  6,  5, 10,  9, 11]

def timeout(min, max):
    return lambda switch, i: random.random() * (max-min) + min

def is_laptop():
    return uuid.getnode() == 180725258261487

def is_local_network():

    process = subprocess.Popen(['networksetup', '-getairportnetwork', 'en0'], stdout=subprocess.PIPE)
    out, err = process.communicate()

    return b'rdv-home' in out

def run_rdv_command_line():

    is_local = is_local_network()

    if not is_local:
        PHILIPS_PATH = 'rdvhome.switches.philips.PhilipsDebugSwitch'
        philips = lambda philips_id, **opts: opts

    else:
        PHILIPS_PATH = 'rdvhome.switches.philips.PhilipsSwitch'
        philips = lambda **opts: dict(
            username  = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
            ipaddress = "192.168.1.179",
            **opts
        )

    if not GPIO:
        GPIO_PATH = 'rdvhome.switches.raspberry.RaspberryDebugSwitch'
    else:
        GPIO_PATH = 'rdvhome.switches.raspberry.RaspberrySwitch'

    def rasp(gpio_relay, gpio_status, **opts):
        assert gpio_status in INPUT
        assert gpio_relay in RELAY1 or gpio_relay in RELAY2
        return dict(gpio_relay = gpio_relay, gpio_status = gpio_status, **opts)

    return execute_from_command_line(
        RASPBERRY_RELAY1 = RELAY1,
        RASPBERRY_RELAY2 = RELAY2,
        RASPBERRY_INPUT  = INPUT,
        INSTALL_DEPENDENCIES = True,
        DEBUG    = is_laptop(), #my laptop everything else is production.
        SWITCHES = {
            GPIO_PATH: (
                rasp(
                    id = 'test_rasp',
                    gpio_relay  = 27,
                    gpio_status = 20,
                ),
            ),
            PHILIPS_PATH: (
                philips(
                    id = 'led_living_room', 
                    name = 'Salone', 
                    ordering =  1, 
                    icon = "🛋", 
                    philips_id = 1, 
                    alias = ['default']
                ),
                philips(
                    id = 'led_tv', 
                    name = 'TV',     
                    ordering =  2, 
                    icon = "📺", 
                    philips_id = 3, 
                    alias = ['default']
                ),
                philips(
                    id = 'led_bedroom', 
                    name = 'Letto',  
                    ordering = 10, 
                    icon = "🛏", 
                    philips_id = 2, 
                    alias = []
                ),
            ),
            'rdvhome.switches.controls.ControlSwitch': (
                dict(
                    id = 'usa',      
                    name = "USA",    
                    ordering = 29, 
                    icon = "🇺🇸", 
                    colors = [
                        dict(hue = 1,    saturation = 1, brightness = 1), 
                        dict(hue = 1,    saturation = 0, brightness = 1),
                        dict(hue = 0.66, saturation = 1, brightness = 1),
                    ], 
                    timeout = 3, 
                    automatic_on = 'default'
                ),
                dict(
                    id = 'natural',    
                    name = "Naturale",  
                    ordering = 30, 
                    icon = "🌞",   
                    colors = [{
                        "hue": 0.12845044632639047,
                        "saturation": 0.5511811023622047,
                        "brightness": 1.0
                    }],
                    automatic_on = 'default'
                ),
                dict(
                    id = 'artic',    
                    name = "Artic",  
                    ordering = 31, 
                    icon = "⛄",   
                    colors = ['#bcf5ff', '#b2ffc5', '#87ffc7']
                ),
                dict(
                    id = 'random',   
                    name = "Random", 
                    ordering = 32, 
                    icon = "❓"
                ),
                dict(
                    id = 'loop',     
                    name = "Random Loop", 
                    ordering = 33, 
                    icon = "➰", 
                    timeout = timeout(30, 60)
                ),
                dict(
                    id = 'hloop',     
                    name = "Random Hipster Loop", 
                    ordering = 34, 
                    icon = "🤓", 
                    timeout = timeout(30, 60),
                    colors = lambda switch, i: dict(
                        saturation = random.random() * 0.25 + 0.15,
                        hue = random.random()
                    )
                ),
                dict(
                    id = 'disco',    
                    name = "Disco",  
                    ordering = 35, 
                    icon = "🌐", 
                    timeout = timeout(0.3, 1.2), 
                    automatic_on = 'default'
                ),
            )
        }
    )

if __name__ == '__main__':
    run_rdv_command_line()