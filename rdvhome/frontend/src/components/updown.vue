<template>
  <label class="toggle">
    <input type="checkbox" @change="toggle" v-model="item[name]">
    <span class="toggle-arrow">
      <span class="arrow one" :class='name'/>
      <span class="arrow two" :class='name'/>
      <span class="arrow three" :class='name'/>
    </span>
  </label>
</template>

<script>

import abstract from '@/components/toggle';

export default {
  extends: abstract,
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="css">

.toggle {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
  transition: .4s;
}

.toggle input {display:none}

.arrow {
  position: absolute;
  left: 14px;
  border: solid var(--border-color);
  border-width: 0 1px 1px 0;
  display: inline-block;
  padding: 4px;
}

.toggle .toggle-arrow {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  -webkit-transition: .4s;
  transition: .4s;
  border:1px solid var(--border-color);
}

.toggle .toggle-arrow .arrow {
  -webkit-transition: .4s;
  transition: .4s;
}

.toggle input:checked + .toggle-arrow .arrow,
.toggle input:checked + .toggle-arrow {
  border-color: rgb(var(--primary-color));
}

.one {
  top: 4px;
  border-color: rgba(var(--primary-color), 0);
}
.one.down {
  top: -1px
}

.two {
  top: 7px;
}
.two.down {
  top: 2px
}
.three {
  top: 10px;
  border-color: rgba(var(--primary-color), 0);
}
.three.down {
  top: 5px
}

.up {
    transform: rotate(-135deg);
    -webkit-transform: rotate(-135deg);
}

.down {
    transform: rotate(45deg);
    -webkit-transform: rotate(45deg);
}
</style>