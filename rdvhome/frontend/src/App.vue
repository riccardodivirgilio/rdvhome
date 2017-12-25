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
            <btn v-bind:color="item.color" v-bind:disabled="item.off || ! item.color">
              {{ item.icon }}
            </btn>
            <slider v-if="!isNaN(item.intensity) && item.on" v-bind:color="item.color"  v-bind:value="item.intensity"  v-on:input="toggle_intensity(item, $event)"/>
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
  border: 1px solid #ddd;
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
  border-bottom:1px solid #ddd;
  color:black;
  position:relative;
  height:$item-size;
  display: flex;
  flex-direction: row;
  align-items: stretch;
}
.list-item > .btn {
  height: $item-size;
  width: $item-size;
  border-bottom:1px solid #ddd;
}
.list-item > .slider {
  z-index: 999;
  width: calc(100% - #{$item-size} - #{$toggle-width} - 2 * #{$item-padding})
}
.list-item > .toggle {
  position: absolute;
  right:  $item-padding;
  width:  $toggle-width;
  height: $toggle-height;
  top:    $item-padding;
  z-index: 1000;
}

.list-item > .title {

  pointer-events: none;
  z-index: 1000;
  position:absolute;
  left: $item-size + $item-padding;
  top: calc(50% - 9px);
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
