# -*- coding: utf-8 -*-

def Client(on_connect = None, on_message = None):
    from paho.mqtt.client import Client as Mqtt

    mqtt = Mqtt()
    mqtt.on_connect = on_connect
    mqtt.on_message = on_message
    mqtt.connect("localhost", 1883, 60)

    return mqtt