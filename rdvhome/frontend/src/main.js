import Vue from 'vue'
import App from './App.vue'

require('rangeinput');

window.vm = new Vue({
  el: '#app',
  render: (h) => h(App)
})