<template>
  <div class="page" v-bind:style="background()">
  <div class="container">

    <home class="panel-home" v-on:toggle="home_toggle($event)" v-bind:switches="switches"></home>

    <div class="panel-switch">
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
              <toggle v-bind:value="item.on" v-on:input="toggle(item, $event)" v-bind:color="item" v-if='item.allow_on'/>
              <updown v-bind:value="item.direction" v-on:input="toggle(item, $event)" v-if='item.allow_direction'/>
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
    </div>
  </div><!-- /.container -->
  </div>
</template>

<script>

import Vue from 'vue'

import loading   from './components/loading';
import toggle    from './components/toggle';
import btn       from './components/btn';
import slider    from './components/slider';
import updown    from './components/updown';
import home      from './components/home';

import debounce  from 'lodash/debounce';

import {hsb_to_css_with_lightness, hsb_to_hsl} from './utils/color';

export default {
  name: 'app',
  components: {
    loading,
    toggle,
    slider,
    updown,
    home,
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
    background: function () {

      var value    = 'repeating-linear-gradient(45deg';
      var initial  = 0;
      var relevant = Object.values(this.switches)
        .filter(item => item.allow_hue)
        .sort((a, b) => (a.ordering - b.ordering))

      relevant.map(item => {
          if (item.on) {
            var color = hsb_to_css_with_lightness(item, 0.15);
          } else {
            var color = 'transparent';
          }

          value   += ', ' + color + ' ' + initial + '%'
          initial += 100 / relevant.length;
          value   += ', ' + color + ' ' + initial + '%'
        })

      if (! initial) {
        return {}
      }

      value += ')'

      return {background:value}
    },
    updateSwitch: function (data) {

      if (this.switches[data.id]) {
        data = Object.assign(this.switches[data.id], data);
      }

      if (! data.advanced_options) {
        data.advanced_options = false;
      }

      Vue.set(this.switches, data.id, data);
    },
    toggle: function (item) {
      if (item.on) {
        this.updateSwitch({id: item.id, advanced_options: false})
      }
      this.send_action(item.id, ! item.on, item.hue, item.saturation, item.brightness)
    },
    home_toggle: function (item) {
      this.toggle(item)
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
$border-color: rgba(70, 70, 70, 0.3);
$body-color:   #000;
$panel-color:  rgba(0, 0, 0, 0.5);

*, *:before, *:after {
  box-sizing: border-box;
  font-family: Helvetica Neue,Helvetica,Arial,sans-serif;
  font-weight: 300;
}

a {
  text-decoration: none;
  color: red;
}

html, body, .page {
  width: 100%;
  min-height: 100%;
  margin:0px;
  padding: 0px;
  display:flex;
  background:$body-color;
  justify-content: space-around;
  color:white;
  position:relative;
}

.connection {
  font-size: 0.8em;
  text-align: center
}

// LAYOUT MOBILE FIRST

.container {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.panel-switch {
    display:flex;
    flex-direction: column;
    width:100%;
    order:1;
}

.panel-home {
    display:flex;
    width:100%;
    order: 2;
    align-items: center;
    padding: 2em;
    background: $panel-color;
}

.panel-home svg {
  width:100%;

}

/*
  ##Device = Tablets, Ipads (portrait)
  ##Screen = B/w 768px to 1024px
*/

@media (min-width: 768px) {

  .container {
    flex-direction: row;
    max-width: 950px;
    background: $panel-color;
    align-items: stretch;
    margin: 3em 0em 3em 0em;
    border: 1em solid $border-color;
  }

  .panel-switch {
    max-width: 400px;
    border-right: 2px solid $border-color;
  }

}

// STARTING LIST STYLES

.list-container {
  width: 100%;
  display: flex;
  flex-direction: column;

}

.list-item {
  border-bottom:1px solid $border-color;
  color:black;
  position:relative;
  display: flex;
  flex-direction: column;
  min-height: $item-size;
  color: white;
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
  top:  $item-size / 2 - 9px;
}
.list-item > .line.slider-hue {
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

</style>