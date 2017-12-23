<template>
  <div class="container">
    <div class="panel">
      <h1>&#127968; RdV</h1>
      <div id="toggles" class="list-container"></div>
      <loading></loading>
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
  data () {
    return {}
  },
  created: function () {

    var W3CWebSocket = require('websocket').w3cwebsocket;

    var client = new W3CWebSocket('ws://localhost:8500/websocket');

    client.onerror = function() {
        console.log('Connection Error');
    };

    client.onopen = function() {
        console.log('WebSocket Client Connected');

        function sendNumber() {
            if (client.readyState === client.OPEN) {
                var number = Math.round(Math.random() * 0xFFFFFF);
                client.send(number.toString());
                setTimeout(sendNumber, 1000);
            }
        }
        sendNumber();
    };

    client.onclose = function() {
        console.log('echo-protocol Client Closed');
    };

    client.onmessage = function(e) {
        if (typeof e.data === 'string') {
            console.log("Received: '" + e.data + "'");
        }
    };

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
}
a {
  text-decoration: none;
  color: red;
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
}
.list-item.on {
  border-right:5px solid lime;
}
.list-item.off {
  border-right:5px solid #ddd;
}
.panel {
    width:400px;
}

footer {
  margin: 30px 15px;
  font-size:0.8em;
  color:#ddd;
  width:100%;
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
