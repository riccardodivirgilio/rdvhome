# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line
from rdvhome.utils.gpio import GPIO
from rdvhome.utils.decorators import to_data

import random
import uuid
import subprocess


RELAY1 = [27, 22, 10,  9, 11,  5,  6, 13]

RELAY2 = [14, 15, 18, 23, 24, 16, 20, 21]

INPUT  = [ 2,  3,  4, 17, 
          25,  8,  7, 12]

def timeout(min, max):
    return lambda switch, i: random.random() * (max-min) + min

def is_laptop():
    return uuid.getnode() == 180725258261487

def is_local_network():

    return False

    process = subprocess.Popen(['networksetup', '-getairportnetwork', 'en0'], stdout=subprocess.PIPE)
    out, err = process.communicate()

    return b'rdv-net' in out

def run_rdv_command_line():

    is_local = is_local_network()

    control = lambda **opts: dict(
        class_path = 'rdvhome.switches.controls.ControlSwitch',
        **opts
    )

    @to_data
    def light(philips_id = None, gpio_relay = None, gpio_status = None, **opts):

        if gpio_relay:
            assert gpio_relay in RELAY1 or gpio_relay in RELAY2
            yield 'gpio_relay', gpio_relay

        if gpio_status:
            assert gpio_status in INPUT
            yield 'gpio_status', gpio_status

        if philips_id:
            yield 'philips_id', philips_id

        if philips_id and is_local:
            yield 'username',  "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W"
            yield 'ipaddress', "192.168.1.179"

        yield 'class_path', 'rdvhome.switches.philips.Light'

        yield from opts.items()

    return execute_from_command_line(
        RASPBERRY_RELAY1 = RELAY1,
        RASPBERRY_RELAY2 = RELAY2,
        RASPBERRY_INPUT  = INPUT,
        INSTALL_DEPENDENCIES = True,
        DEBUG    = is_laptop(), #my laptop everything else is production.
        SWITCHES = [

            light(
                id = 'led_living_room', 
                name = 'Salone Led', 
                ordering =  8, 
                icon = "🛋", 
                philips_id = 1, 
                alias = ['default']
            ),
            light(
                id = 'led_tv', 
                name = 'TV Led',     
                ordering =  10, 
                icon = "📺", 
                philips_id = 3, 
                alias = ['default']
            ),
            light(
                id = 'led_bedroom', 
                name = 'Letto Led',  
                ordering = 12, 
                icon = "🛏", 
                philips_id = 2, 
                alias = []
            ),

            light(
                id = 'spotlight_living_room', 
                name = 'Salone', 
                ordering =  9, 
                icon = "🛋", 
                alias = [],
                gpio_relay  = RELAY1[0],
                gpio_status = INPUT[0],
            ),
            light(
                id = 'spotlight_tv', 
                name = 'TV',     
                ordering =  11, 
                icon = "📺", 
                alias = [],
                gpio_relay  = RELAY1[1],
                gpio_status = INPUT[1],
            ),
            light(
                id = 'spotlight_bedroom', 
                name = 'Letto',  
                ordering = 13, 
                icon = "🛏", 
                alias = [],
                gpio_relay  = RELAY1[2],
                gpio_status = INPUT[2],
            ),
            light(
                id = 'spotlight_entrance', 
                name = 'Entrata',  
                ordering = 14, 
                icon = "🚪", 
                alias = [],
                gpio_relay  = RELAY1[3],
                gpio_status = INPUT[3],
            ),
            light(
                id = 'spotlight_kitchen', 
                name = 'Cucina',  
                ordering = 15, 
                icon = "🍽", 
                alias = [],
                gpio_relay  = RELAY1[4],
                gpio_status = INPUT[4],
            ),
            light(
                id = 'spotlight_room', 
                name = 'Studio',  
                ordering = 16, 
                icon = "📚", 
                alias = [],
                gpio_relay  = RELAY1[5],
                gpio_status = INPUT[5],
            ),
            control(
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
            control(
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
            control(
                id = 'artic',    
                name = "Artic",  
                ordering = 31, 
                icon = "⛄",   
                colors = ['#bcf5ff', '#b2ffc5', '#87ffc7']
            ),
            control(
                id = 'random',   
                name = "Random", 
                ordering = 32, 
                icon = "❓"
            ),
            control(
                id = 'loop',     
                name = "Random Loop", 
                ordering = 33, 
                icon = "➰", 
                timeout = timeout(30, 60)
            ),
            control(
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
            control(
                id = 'disco',    
                name = "Disco",  
                ordering = 35, 
                icon = "🌐", 
                timeout = timeout(0.3, 1.2), 
                automatic_on = 'default'
            ),
        ]
    )

if __name__ == '__main__':
    run_rdv_command_line()