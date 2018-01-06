<template>
  <div class="container">
    <div class="panel">
      <h1>&#127968; Lighttardo</h1>
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
            <div class="line">
              <btn v.bind:value="item.advanced_options" v-bind:color="item" v-bind:disabled="item.off || ! item.allow_hue" v-on:input="toggle_advanced_options(item, $event)">
                <div v-if="item.advanced_options && item.on" style="padding-top:3px">&times;</div>
                <div v-else>{{ item.icon }}</div>
              </btn>
              <slider v-if="item.on && item.allow_brightness" v-bind:color="item" v-bind:value="item.brightness" v-on:input="toggle_hsb(item, null, null, $event)"/>
              <div class="title">{{ item.name }}</div>
              <toggle v-bind:value="item.on" v-on:input="toggle(item, $event)" v-bind:color="item"/>
            </div>
            <div v-if="item.on && item.advanced_options && item.allow_hue" class="line slider-hue">
              <slider v-bind:value="item.hue" v-on:input="toggle_hsb(item, $event, null, null)"/>
            </div>
            <div v-if="item.on && item.advanced_options && item.allow_saturation" class="line slider-saturation" v-bind:style="{background:
              'linear-gradient(to right, white 0%, '+to_css({hue: item.hue, saturation: 1})+' 100%)'}">
              <slider v-bind:value="item.saturation" v-on:input="toggle_hsb(item, null, $event, null)"/>
            </div>
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

import Vue from 'vue'

import loading  from './components/loading';
import toggle   from './components/toggle';
import btn      from './components/btn';
import slider   from './components/slider';
import debounce from 'lodash/debounce';

import {hsb_to_css_with_lightness} from './utils/color';

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
    to_css: hsb_to_css_with_lightness,
    updateSwitch: function (data) {

      if (this.switches[data.id]) {
        data = Object.assign(this.switches[data.id], data);
      }

      if (! data.advanced_options) {
        data.advanced_options = false;
      }

      Vue.set(this.switches, data.id, data);
    },
    toggle: function (item, value) {

      if (item.on) {
        this.updateSwitch({id: item.id, advanced_options: false})
      }

      this.send_action(item.id, ! item.on, item.hue, item.saturation, item.brightness)
    },
    format_hsb_value: function(value) {
      if (value || value == 0) {
        return Math.round(value * 100)
      }
      return '-'
    },
    format_on_value: function(value) {
      if (value == true) {
        return 'on'
      }
      if (value == false) {
        return 'off'
      }
      return '-'
    },
    send_action: function(id, on, h, s, b) {
      const url = '/switch/' + id + '/' + this.format_on_value(on) + '/' + this.format_hsb_value(h) + '/' + this.format_hsb_value(s) + '/' + this.format_hsb_value(b);
      this.ws.send(url)
    },
    toggle_hsb: debounce(
      function(item, h, s, b) {
        this.send_action(item.id, null, h, s, b)
      },
      200
    ),
    toggle_advanced_options: function(item, value) {
      this.updateSwitch({id: item.id, advanced_options: ! item.advanced_options})
    },
    connect: function(force) {

      if (force) {
        this.reconnect  = 1;
      } else {
        this.reconnect += 1;
      }

      this.connected = false;
      this.ws        = null;

      console.log("Attempting to connect to ws number " + this.reconnect)

      if (this.reconnect < 4) {
        this.ws = new WebSocket('ws://'+ window.location.hostname +':8500/websocket');

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
$btn-width: $item-size + 20px;

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

@media only screen and (max-width: 500px) {
    h1 {
        display: none
    }
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
  flex-direction: column;
  min-height: $item-size;
}
.list-item > .line {
  display: flex;
  flex-direction: row;
  position:relative
}
.list-item > .line > .btn {
  width: $btn-width;
  height: auto;
}
.list-item > .line > .slider {
  width: calc(100% - #{$btn-width} - #{$toggle-width} - 2 * #{$item-padding});
  height: $item-size;
  display:flex;
  flex-direction: column;
}

.list-item > .line.slider-saturation > .slider,
.list-item > .line.slider-hue > .slider {
  width: 100%
}
.list-item > .line:not(:last-child) {
  border-bottom:1px solid $border-color
}

.list-item > .line > .toggle {
  position: absolute;
  right:  $item-padding;
  width:  $toggle-width;
  height: $toggle-height;
  top:    $item-padding;
}

.list-item > .line > .title {
  pointer-events: none;
  position:absolute;
  left: $btn-width + $item-padding;
  top:  $item-size / 2 - 9px
}
.slider-hue {
     background: linear-gradient(
      to right, 
      hsl(  0, 100%, 50%)   0.0000%, 
      hsl( 60, 100%, 50%)  16.6667%, 
      hsl(120, 100%, 50%)  33.3333%, 
      hsl(180, 100%, 50%)  50.0000%, 
      hsl(240, 100%, 50%)  66.6667%, 
      hsl(300, 100%, 50%)  83.3333%, 
      hsl(360, 100%, 50%) 100.0000%
    );
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