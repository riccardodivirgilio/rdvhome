<template>
  <div class="container">
    <div class="panel">
      <h1>&#127968; RdV</h1>
      <template v-if="switches.length == 0 || ! connected">
        <loading v-bind:class="{active: reconnect < reconnect_limit}"></loading>
        <div class="connection" v-if="reconnect < reconnect_limit">
          Connection in progress... 
        </div>
        <div class="connection" v-else>
          Disconnected. <a href="/connect" v-on:click.stop.prevent="connect(true)">Try again &rarr;</a>
        </div>
      </template>
      <template v-else>
        <div id="toggles" class="list-container" >
          <a v-for="item in switches" class="list-item" v-bind:class="{on: item.on, off: item.off}" :key="item.id" v-bind:style="{order: item.ordering}">
            <btn v-bind:color="item.color" v-bind:disabled="item.off || ! item.color" v-on:input="toggle_colorpicker(item, $event)">
              <div v-if="item.colorpicker && item.on" style="padding-top:3px">&times;</div>
              <div v-else>{{ item.icon }}</div>
            </btn>
            <div class="sliders" v-if="!isNaN(item.intensity) && item.on">
              <slider v-bind:color="item.color"  v-bind:value="item.intensity"  v-on:input="toggle_intensity(item, $event)"/>
              <slider v-if="item.colorpicker" value="0.5" class="hue"/>
              <slider v-if="item.colorpicker" value="0.3" v-bind:color="item.color"/>
            </div>
            <div class="title">{{ item.name }}</div>
            <toggle v-bind:value="item.on" v-on:input="toggle(item, $event)" v-bind:color="item.color"/>
          </a>
        </div>
      </template>
      <footer class="footer">
        Made with <span style="font-size:1.2em">&hearts;</span> in San Paolo.
      </footer>
    </div>
  </div><!-- /.container -->
</template>

<script>

import loading from './components/loading';
import toggle  from './components/toggle';
import btn     from './components/btn';
import slider  from './components/slider';

export default {
  name: 'app',
  components: {
    loading,
    toggle,
    slider,
    btn
  },
  data: function() {
    return {
      switches: {},
      reconnect: 0,
      connected: false,
      reconnect_limit: 4
    }
  },
  methods: {
    updateSwitch: function (data) {

      if (! this.switches[data.id]) {
        this.switches[data.id] = data;
      } else {
        this.switches[data.id] = Object.assign(this.switches[data.id], data)
      }
      this.$forceUpdate();
    },
    toggle: function (item, value) {
      this.ws.send('/switch/' + item.id + '/' + (item.on ? 'off' : 'on'))
    },
    toggle_intensity: function(item, value) {
      this.ws.send('/switch/' + item.id + '/intensity/' + Math.round(value * 100))
    },
    toggle_colorpicker: function(item, value) {
      this.switches[item.id]['colorpicker'] = value
      this.$forceUpdate();
    },
    connect: function(force) {

      if (force) {
        this.reconnect = 1
      } else {
        this.reconnect += 1;
      }

      this.connected = false;
      this.ws        = null;

      console.log("Attempting to connect to ws number " + this.reconnect)

      if (this.reconnect < 4) {
        this.ws = new WebSocket('ws://localhost:8500/websocket');

        this.ws.onerror = (e) => {
            console.log('Connection Error');
            console.log(e)
            this.connected = false;
            setTimeout(() => {this.connect()}, 1000);
        };

        this.ws.onopen = (e) => {
            console.log('WebSocket Client Connected');
            console.log(e)
            this.reconnect = 0;
            this.connected = true;
            this.ws.send('/switch');
        };

        this.ws.onclose = (e) => {
            console.log('WebSocket Client Disconnected');
            console.log(e)
            this.connected = false;
            setTimeout(() => {this.connect()}, 1000);
        };

        this.ws.onmessage = (e) => {
            if (typeof e.data === 'string') {
                this.updateSwitch(JSON.parse(e.data))
            }
        };
      }
    }
  },

  created: function() {
    this.connect()
  }
}
</script>

<style lang="scss">

$item-size: 50px;
$item-padding: 15px;

$toggle-height: $item-size - 2 * $item-padding;
$toggle-width:  $toggle-height * 2;
$border-color: #ddd;

*, *:before, *:after {
  box-sizing: border-box;
  font-family: Helvetica Neue,Helvetica,Arial,sans-serif;
  font-weight: 300;
}
body {
  margin:0px;
  padding: 0px
}
h1 {
  padding: 0 15px;
  font-weight: 200;
  color: gray;
  text-align: center
}
a {
  text-decoration: none;
  color: red;
}
.connection {
  font-size: 0.8em;
  text-align: center
}
.container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  align-items: center;
}
.list-container {
  display: flex;
  flex-direction: column;
  border: 1px solid $border-color;
  border-bottom: none
}

.panel {
    width:400px;
}

footer {
  margin-top: 30px;
  font-size:0.8em;
  color:#ccc;
  width:100%;
  text-align: center;
}

@media only screen and (max-width: 400px)  {
  .panel {
    width:100%;
  }
  .list-container {
    border-left:none;
    border-right:none;
  }
}

.list-item {
  border-bottom:1px solid $border-color;
  color:black;
  position:relative;
  display: flex;
  flex-direction: row;
  min-height: $item-size;
}
.list-item > .btn {
  width: $item-size;
  height: auto;
}
.list-item > .sliders {
  width: calc(100% - #{$item-size} - #{$toggle-width} - 2 * #{$item-padding});
  display:flex;
  flex-direction: column;
}
.list-item > .sliders > .slider {
  height: $item-size;
}
.list-item > .sliders > .slider:not(:last-child) {
  border-bottom: 1px solid $border-color;
}

.list-item > .toggle {
  position: absolute;
  right:  $item-padding;
  width:  $toggle-width;
  height: $toggle-height;
  top:    $item-padding;
}

.list-item > .title {
  pointer-events: none;
  position:absolute;
  left: $item-size + $item-padding;
  top: $item-size / 2 - 9px
}
.hue {
     background: linear-gradient(to right, #ff0000 0%, #ffff00 17%, #00ff00 33%, #00ffff 50%, #0000ff 67%, #ff00ff 83%, #ff0000 100%); 
}
.hue-overlay {
    background: linear-gradient(to right, #ff0000 0%, #ffff00 17%, #00ff00 33%, #00ffff 50%, #0000ff 67%, #ff00ff 83%, #ff0000 100%);
    position:absolute;
    width:100%;
    height: 100%;
    pointer-events:none;
    top:0px;
    left:0px;
}

@keyframes off {
    0% { background-color: #efefef; }
    100% { background-color: none; }
}

.waiting {
  animation: waiting 2s ease-out;
  animation-iteration-count: infinite;
}

@keyframes waiting {
    0% { background-color: none; }
    50% { background-color: #e0eaf9; }
    100% { background-color: none; }
}
</style>
