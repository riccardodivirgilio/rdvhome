<template>

  <label class="toggle" v-bind:style="{backgroundColor: color ? to_css(color) : 'white'}">
    <input type="checkbox" @change="toggle" :checked="value" :name="name">
    <span class="toggle-button"></span>
  </label>

</template>

<script>

import {hsb_to_css_with_lightness} from '../utils/color';

export default {
  name: 'toggle',
  props: ['name', 'color', 'value'],
  data: function() {
    return {
    }
  },
  methods: {
      to_css: hsb_to_css_with_lightness,
      toggle (e) {
          this.$emit('input', this.value);
      }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>

.toggle {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
  transition: .4s;
}

.toggle input {display:none;}

.toggle .toggle-button {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  -webkit-transition: .4s;
  transition: .4s;
  border:1px solid #ddd;
}

.toggle .toggle-button:before {
  position: absolute;
  content: "";
  height: 100%;
  width: 50%;
  left: 0px;
  bottom: 0px;

  -webkit-transition: .4s;
  transition: .4s;
  border:           1px solid #ddd;
  background-color: rgba(255, 255, 255, 0.5);
  border-color:     rgba(  0,   0,   0, 0.5);
}

.toggle input:not(:checked) + .toggle-button {
  background-color: rgba(  0,   0,   0, 0.5);
  border-color:     rgba(255, 255, 255, 0.5);
}

.toggle input:checked + .toggle-button:before {
  -webkit-transform: translateX(100%);
  -ms-transform: translateX(100%);
  transform: translateX(100%);
}
</style>