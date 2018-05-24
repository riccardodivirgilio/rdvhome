# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line
from rdvhome.utils.gpio import GPIO
from rdvhome.utils.decorators import to_data

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

    control = lambda **opts: dict(
        class_path = 'rdvhome.switches.controls.ControlSwitch',
        **opts
    )

    @to_data
    def switch(philips_id = None, gpio_relay = None, gpio_status = None, **opts):

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
            switch(
                id = 'test_rasp',
                gpio_relay  = 27,
                gpio_status = 20,
                ordering    =  1,
            ),
            switch(
                id = 'test_philp_rasp',
                gpio_relay  = 17,
                gpio_status =  5,
                philips_id  = 90,
                ordering    =  2,
            ),
            switch(
                id = 'led_living_room', 
                name = 'Salone', 
                ordering =  8, 
                icon = "🛋", 
                philips_id = 1, 
                alias = ['default']
            ),
            switch(
                id = 'led_tv', 
                name = 'TV',     
                ordering =  9, 
                icon = "📺", 
                philips_id = 3, 
                alias = ['default']
            ),
            switch(
                id = 'led_bedroom', 
                name = 'Letto',  
                ordering = 10, 
                icon = "🛏", 
                philips_id = 2, 
                alias = []
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