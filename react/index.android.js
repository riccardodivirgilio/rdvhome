/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 * @flow
 */

import init from 'react_native_mqtt';
import { AsyncStorage } from 'react-native';

import React, { Component } from 'react';
import { AppRegistry, StyleSheet, ListView, Text, View } from 'react-native';

init({
  size: 10000,
  storageBackend: AsyncStorage,
  defaultExpires: 1000 * 3600 * 24,
  enableCache: true,
  sync : {}
});

const styles = StyleSheet.create({
  bigblue: {
    color: 'blue',
    fontWeight: 'bold',
    fontSize: 30,
  },
  red: {
    color: 'red',
  },
});

class Toggle extends Component {
  render() {
    return (
      <Text>{this.props.text}</Text>
    );
  }
}

class ListViewBasics extends Component {
  // Initialize the hardcoded data
  constructor(props) {
    super(props);
    const ds = new ListView.DataSource({rowHasChanged: (r1, r2) => r1 !== r2});
    this.state = {
      message:'Started...',
      dataSource: ds.cloneWithRows([])
    };

    var app = this;
    var client = new Paho.MQTT.Client('iot.eclipse.org', 443, 'unique_client_name');

    function onConnect() {
      app.setState({ message: "Connected" });
      var message = new Paho.MQTT.Message("/switch");
      message.destinationName = "c-63HhqFG9QoKRbq47q0D48N";
      client.subscribe("s-63HhqFG9QoKRbq47q0D48N");
      client.send(message);
    }

    function onFailure(e) {
      console.warn(JSON.stringify(e))
    }

    function onConnectionLost(e) {
      if (e.errorCode !== 0) {
        console.warn(JSON.stringify(e))
      }
    }

    function onMessageArrived(message) {
      var data = JSON.parse(message.payloadString);
      app.setState({ dataSource: ds.cloneWithRows(data.toggles) });
    }

    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;
    client.connect({onSuccess:onConnect, onFailure:onFailure, useSSL:true});

  }
  render() {
    return (
      <View style={{flex: 1, paddingTop: 22}}>
        <Text style={[styles.bigblue, styles.red]}>{this.state.message}</Text>
        <ListView
          dataSource={this.state.dataSource}
          renderRow={(toggle) => <Toggle text={toggle.name}></Toggle>}
        />
      </View>
    );
  }

}

// App registration and rendering
AppRegistry.registerComponent('rdvhome', () => ListViewBasics);
