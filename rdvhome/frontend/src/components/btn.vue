<template>

  <label class="btn" :class="{disabled: disabled}">
    <input type="checkbox" @change="toggle" v-model="item[name]">
    <div class="title"><slot/></div>
  </label>

</template>

<script>

import abstract from './toggle';

export default {
  name: 'slider',
  props: ['disabled'],
  extends: abstract,
}

</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="css">

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
</style>