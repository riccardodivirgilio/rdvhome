<template>

  <label class="btn" v-bind:class="{disabled: disabled}" v-bind:style="{backgroundColor: (! disabled && color) ? color : 'white'}">
    <input type="checkbox" @change="toggle" :checked="value" :disabled="disabled" :name="name">
    <span class="btn-inner"></span>
    <div class="title"><slot></slot></div>
  </label>

</template>

<script>
export default {
  name: 'btn',
  props: ['name', 'value', 'color', 'disabled'],
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

.btn {
  position: relative;
  display: flex;
  align-items: center;
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
  text-align: center;
  width: 100%;
  margin-top:1px;
  position: relative;

}

.btn .btn-inner {
  position: absolute;
  width: 100%;
  height: 100%;
  
}

.btn input:checked + .btn-inner {
  background-color: rgba(255, 255, 255, 0.2);
}

</style>