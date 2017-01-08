# -*- coding: utf-8 -*-

def Client(on_connect = None, on_message = None):
    from paho.mqtt.client import Client as Mqtt
    mqtt = Mqtt()
    mqtt.on_connect = on_connect
    mqtt.on_message = on_message
    mqtt.username_pw_set('owflekio', '0aeZc50ixVbT')
    mqtt.connect("m21.cloudmqtt.com", 16494, 60)
    #mqtt.connect("localhost", 1883, 60)
    return mqtt