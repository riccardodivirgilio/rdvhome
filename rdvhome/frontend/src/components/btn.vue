<template>

  <label class="btn" v-bind:class="{disabled: disabled}">
    <input type="checkbox" @change="toggle" v-model="value" v-bind:disabled="disabled" v-bind:name="name">
    <span class="btn-inner" v-bind:style="{backgroundColor: (! disabled && color) ? color : 'white'}"></span>
    <div class="title"><slot></slot></div>
  </label>

</template>

<script>
export default {
  name: 'btn',
  props: ['name', 'color', 'disabled'],
  data: function() {
    return {

    }
  },
  methods: {
      toggle (e) {
          this.$emit('input', this.value);
      }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>

.btn {
  position: relative;
  display: flex;
  align-items: top;
  justify-content: center;
  width:  30px;
  height: 30px;
  transition: .2s;
  cursor: pointer;
}
.btn.disabled {
  cursor: initial;
}

.btn input {display:none;}

.btn .title {
  padding-top:10px;
  text-align: center;
  width: 100%;
  margin-top:1px;
  position: relative;
}

.btn .btn-inner {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0.15;
}

.btn input:checked + .btn-inner {
  
}

</style>