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
          <a v-for="item in switches" class="list-item" :key="item.id" v-on:click.stop.prevent="open(item.action)" v-bind:href="item.action" v-bind:style="{order: item.ordering}">
            {{ item.name }}
            <div v-bind:class="{on: item.on, off: item.off}" v-bind:style="{backgroundColor: item.on ? item.color : '#ddd'}">
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

import loading from './components/loading';

export default {
  name: 'app',
  components: {
    loading
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
    open: function (url) {
      if (url) {
        this.ws.send(url)
      }
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

        this.ws.onerror = () => {
            console.log('Connection Error');

            setTimeout(() => {this.connect()}, 1000);

        };

        this.ws.onopen = () => {
            console.log('WebSocket Client Connected');
            this.reconnect = 0;
            this.connected = true;
            this.ws.send('/switch');
        };

        this.ws.onclose = () => {
            console.log('WebSocket Client Disconnected');
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
.list-item {
  padding:15px;
  border-bottom:1px solid #ddd;
  color:black;
  position:relative;
}
.list-item .on,
.list-item .off {
  position:absolute;
  right: 0px;
  top:0px;
  height: 100%;
  width: 7px;
  border-left: 1px solid #ddd;
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

.on {
  animation: on 0.3s ease-out;
  animation-iteration-count: 1;
}

@keyframes on {
    0% { background-color: #edffd3; }
    100% { background-color: none; }
}

.off {
  animation: off 0.3s ease-out;
  animation-iteration-count: 1;
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
