import Vue from 'vue'
import App from './App.vue'


window.vm = new Vue({
  el: '#app',
  render: function(h) {return h(App)}
})