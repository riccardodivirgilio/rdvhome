

<script>

import switches  from '../data/switches';
import debounce  from '../utils/debounce';

import values    from 'rfuncs/functions/values'
import merge     from 'rfuncs/functions/merge'
import map       from 'rfuncs/functions/map'
import scan      from 'rfuncs/functions/scan'

export default {
  name: 'app',
  data: function() {
    return {
      switches: switches,
      reconnect: 0,
      connected: false,
      reconnect_limit: 4
    }
  },
  methods: {
    updateSwitch: function (data) {
      this.switches[data.id] = merge(
          {advanced_options: false},
          this.switches[data.id] || {},
          data
        )
    },
    toggle: debounce(
      function (item) {
        this.send_action(item.id, {
          mode:       this.format_on_value(item.on),
          hue:        this.format_hsb_value(item.hue),
          brightness: this.format_hsb_value(item.brightness),
          saturation: this.format_hsb_value(item.saturation),
        })
      }
    ),
    toggle_hsb: debounce(
      function(item, name) {
        this.send_action(item.id, {[name]: this.format_hsb_value(item[name])})
      },
      200
    ),
    toggle_direction: function (item, direction) {
      this.send_action(item.id, {
        mode: this.format_direction_value(item[direction], direction),
      })
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
    format_direction_value: function(value, direction) {
      if (value == true) {
        return direction
      }
      if (value == false) {
        return 'stop'
      }
      return '-'
    },
    send_action: function(id, data) {

      console.log('SENDING ITEM')
      console.log(id)
      console.log(data)

      const url = '/switch/' + id + '/set?' + values(
          map(
          (v, k) => k + '=' + encodeURIComponent(v),
          data
        )
      ).join('&')

      //+ this.format_on_value(on) + '/' + this.format_hsb_value(h) + '/' + this.format_hsb_value(s) + '/' + this.format_hsb_value(b);
      this.ws.send(url)
    },
    connect: function(force) {

      if (force) {
        this.reconnect  = 1;
      } else {
        this.reconnect += 1;
      }

      this.connected = false;
      this.ws        = null;

      console.log("Attempting to connect to WS number " + this.reconnect)

      if (this.reconnect < 4) {

        if (typeof window == 'undefined' || window.location.protocol == 'file:') {
          this.ws = this.websocket('ws://rdvhome.local:8500/websocket');
        } else {
          this.ws = this.websocket('ws://'+ window.location.hostname +':8500/websocket');
        }

        this.ws.addEventListener('error', e => {
            console.log('Connection Error');
            console.log(e)
            this.connected = false;
            setTimeout(() => {this.connect()}, 1000);
        });

        this.ws.addEventListener('open', e => {
            console.log('WebSocket Client Connected');
            console.log(e)
            this.reconnect = 0;
            this.connected = true;
            this.ws.send('/switch');
        });

        this.ws.addEventListener('close',  e => {
            console.log('WebSocket Client Disconnected');
            console.log(e)
            this.connected = false;
            setTimeout(() => {this.connect()}, 1000);
        });

        this.ws.addEventListener('message', e => {
            if (typeof e.data === 'string') {
              const data = JSON.parse(e.data)
              console.log('Incoming:')
              console.log(data)
              this.updateSwitch(data)
            }
        });

        console.log('OPENIng')
        console.log(this.ws.readyState)
        console.log(this.ws.readyState)
      }
    },
    websocket: function(arg) {
      return new WebSocket(arg);
    },

  },
  created: function() {

    console.log('app loaded, start connect')
    this.connect()
  }
}
</script>
