package com.rdv.client;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;

import android.content.Context;
import android.widget.Toast;

import com.rdv.client.Settings;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

public class Toggle extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_toggle);

        final MqttAndroidClient mqttAndroidClient = new MqttAndroidClient(
                this.getApplicationContext(),
                Settings.MQTT_BROKER_URL,
                "androidSampleClient"
        );
        mqttAndroidClient.setCallback(new MqttCallback() {
            @Override
            public void connectionLost(Throwable cause) {
                Toast toast = Toast.makeText(
                        getApplicationContext(),
                        "Connection was lost!",
                        Toast.LENGTH_SHORT
                );
                toast.show();
            }

            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {


                Toast toast = Toast.makeText(
                        getApplicationContext(),
                        "Message Arrived!: " + topic + ": " + new String(message.getPayload()),
                        Toast.LENGTH_SHORT
                );
                toast.show();

            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                Toast toast = Toast.makeText(
                        getApplicationContext(),
                        "Delivery Complete!",
                        Toast.LENGTH_SHORT
                );
                toast.show();
            }
        });

        try {
            mqttAndroidClient.connect(null, new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {

                    Toast toast = Toast.makeText(
                            getApplicationContext(),
                            "Connection Success!",
                            Toast.LENGTH_SHORT
                    );
                    toast.show();
                    try {
                        mqttAndroidClient.subscribe(Settings.MQTT_CHANNEL_STATUS, 0);
                        mqttAndroidClient.publish(Settings.MQTT_CHANNEL_COMMAND, new MqttMessage(Settings.MQTT_INITIAL_COMMAND.getBytes()));
                    } catch (MqttException ex) {

                    }

                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Toast toast = Toast.makeText(
                            getApplicationContext(),
                            "Connection Failure!",
                            Toast.LENGTH_SHORT
                    );
                    toast.show();
                }
            });
        } catch (MqttException ex) {

        }


    }

}
