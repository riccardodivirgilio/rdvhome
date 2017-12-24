<template>

  <label class="toggle" v-bind:style="{backgroundColor: color ? color : 'white'}">
    <input type="checkbox" @change="toggle" :checked="value" :name="name">
    <span class="slider"></span>
  </label>

</template>

<script>
export default {
  name: 'toggle',
  props: ['name', 'value', 'color'],
  data: function() {
    return {

    }
  },
  methods: {
      toggle (e) {
          this.value = ! this.value;
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
  width: 50px;
  height: 26px;
}

.toggle input {display:none;}

.slider {
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

.slider:before {
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

input:not(:checked) + .slider {
  background-color: rgba(  0,   0,   0, 0.5);
  border-color:     rgba(255, 255, 255, 0.5);
}

input:checked + .slider:before {
  -webkit-transform: translateX(100%);
  -ms-transform: translateX(100%);
  transform: translateX(100%);
}

/* Rounded sliders */
.slider.round {
  border-radius: 34px;
}

.slider.round:before {
  border-radius: 50%;
}
</style>