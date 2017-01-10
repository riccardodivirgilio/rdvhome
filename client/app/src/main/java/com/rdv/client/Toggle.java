package com.rdv.client;

import java.util.HashMap;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

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
import android.widget.AdapterView.OnItemClickListener;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;

import java.util.UUID;

public class Toggle extends AppCompatActivity {

    HashMap<String, HashMap<String, String>> toggleMap = new HashMap<>();
    ArrayList<HashMap<String, String>> toggleList;
    MqttAndroidClient mqttAndroidClient;


    private ListView lv;


    public void publish(String msg) {
        try {
            mqttAndroidClient.subscribe(Settings.MQTT_CHANNEL_STATUS, 0);
            mqttAndroidClient.publish(
                    Settings.MQTT_CHANNEL_COMMAND,
                    new MqttMessage(msg.getBytes())
            );
        } catch (MqttException ex) {

        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_toggle);


        mqttAndroidClient = new MqttAndroidClient(
                this.getApplicationContext(),
                Settings.MQTT_BROKER_URL,
                UUID.randomUUID().toString()
        );

        lv = (ListView) findViewById(R.id.list);

        lv.setOnItemClickListener(new OnItemClickListener()
        {
            @Override
            public void onItemClick(AdapterView<?> a, View v, int position, long id)
            {
                publish(toggleList.get(position).get("action"));
            }
        });

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
                        String key = toggles.names().getString(i);
                        JSONObject t = toggles.getJSONObject(key);

                        // tmp hash map for single toggle
                        HashMap<String, String> toggle = new HashMap<>();

                        // adding each child node to HashMap key => value

                        toggle.put("name",   t.getString("name"));
                        toggle.put("on",     t.getString("on"));
                        toggle.put("order",  t.getString("order"));
                        toggle.put("action", t.getString("action"));

                        // adding toggle to toggle list
                        toggleMap.put(key, toggle);

                    }

                    toggleList = new ArrayList(toggleMap.values());

                    Collections.sort(toggleList, new Comparator<HashMap<String, String>>() {
                        @Override
                        public int compare(HashMap<String, String> o1, HashMap<String, String> o2) {
                            return o1.get("order").compareTo(o2.get("order"));
                        }
                    });

                    ListAdapter adapter = new SimpleAdapter(
                            Toggle.this,
                            toggleList,
                            R.layout.toggle,
                            new String[]{"name", "order", "on", "action"},
                            new int[]{R.id.name, R.id.order, R.id.on, R.id.action}
                    );

                    lv.setAdapter(adapter);

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

                    } catch (MqttException ex) {

                    }
                    publish(Settings.MQTT_INITIAL_COMMAND);
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
