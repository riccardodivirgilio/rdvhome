package com.rdv.client;

import java.util.HashMap;
import java.util.ArrayList;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;

import android.content.Context;
import android.widget.Toast;

import com.rdv.client.Settings;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import android.widget.ListAdapter;
import android.widget.ListView;
import android.widget.SimpleAdapter;
import java.util.UUID;

public class Toggle extends AppCompatActivity {

    ArrayList<HashMap<String, String>> toggleList;
    private ListView lv;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_toggle);

        toggleList = new ArrayList<>();

        lv = (ListView) findViewById(R.id.list);

        final MqttAndroidClient mqttAndroidClient = new MqttAndroidClient(
                this.getApplicationContext(),
                Settings.MQTT_BROKER_URL,
                UUID.randomUUID().toString()
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

                String jsonStr = new String(message.getPayload());

                try {
                    JSONObject jsonObj = new JSONObject(jsonStr);

                    // Getting JSON Array node
                    JSONObject toggles = jsonObj.getJSONObject("toggles");

                    // looping through All Contacts
                    for (int i = 0; i < toggles.names().length(); i++) {
                        JSONObject t = toggles.getJSONObject(toggles.names().getString(i));

                        // tmp hash map for single toggle
                        HashMap<String, String> toggle = new HashMap<>();

                        // adding each child node to HashMap key => value

                        toggle.put("name",   t.getString("name"));
                        toggle.put("on", t.getString("on"));
                        toggle.put("order",   t.getString("order"));

                        // adding toggle to toggle list
                        toggleList.add(toggle);

                        ListAdapter adapter = new SimpleAdapter(
                                Toggle.this,
                                toggleList,
                                R.layout.toggle,
                                new String[]{"name", "order", "on"},
                                new int[]{R.id.name, R.id.order, R.id.on});

                        lv.setAdapter(adapter);

                    }
                } catch (final JSONException e) {
                    Toast toast = Toast.makeText(
                            getApplicationContext(),
                            "Json parsing error: " + e.getMessage(),
                            Toast.LENGTH_SHORT
                    );
                    toast.show();
                }
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                //Toast toast = Toast.makeText(
                //        getApplicationContext(),
                //        "Delivery Complete!",
                //        Toast.LENGTH_SHORT
                //);
                //toast.show();
            }
        });

        try {
            mqttAndroidClient.connect(null, new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    //Toast toast = Toast.makeText(
                    //        getApplicationContext(),
                    //        "Connection Success!",
                    //        Toast.LENGTH_SHORT
                    //);
                    //toast.show();
                    try {
                        mqttAndroidClient.subscribe(Settings.MQTT_CHANNEL_STATUS, 0);
                        mqttAndroidClient.publish(
                                Settings.MQTT_CHANNEL_COMMAND,
                                new MqttMessage(Settings.MQTT_INITIAL_COMMAND.getBytes())
                        );
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
