

// Constant utility class
package com.rdv.client;

public class Settings {
    private Settings() { }  // Prevents instantiation

    public static final String MQTT_CHANNEL_COMMAND = "c-63HhqFG9QoKRbq47q0D48N";
    public static final String MQTT_CHANNEL_STATUS  = "s-63HhqFG9QoKRbq47q0D48N";
    public static final String MQTT_BROKER_URL = "tcp://iot.eclipse.org:1883";
    public static final String MQTT_BROKER_PASSWORD = "";
    public static final String MQTT_BROKER_USERNAME = "";
    public static final String MQTT_INITIAL_COMMAND = "/switch";

}

