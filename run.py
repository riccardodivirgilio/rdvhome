# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from rdvhome.cli.main import execute_from_command_line

import random
import uuid

def timeout(min, max):
    return lambda switch, i: random.random() * (max-min) + min

def is_laptop():
    return uuid.getnode() == 180725258261487

def run_rdv_command_line():

    philips = lambda id, name, **opts: dict(
        id        = id,
        name      = name,
        username  = "Ro1Y0u6kFH-vgkwdbYWAk8wQNUaXM3ODosHaHG8W",
        ipaddress = "192.168.1.179",
        **opts
    )

    return execute_from_command_line(
        INSTALL_DEPENDENCIES = True,
        DEBUG    = is_laptop(), #my laptop everything else is production.
        SWITCHES = {
            'rdvhome.switches.philips.PhilipsSwitch': (
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