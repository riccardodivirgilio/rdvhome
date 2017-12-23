import Vue from 'vue'
import App from './App.vue'
import VueNativeSock from 'vue-native-websocket'

Vue.use(VueNativeSock, 'ws://localhost:8500/websocket');

window.vm = new Vue({
  el: '#app',
  render: function(h) {return h(App)}
})