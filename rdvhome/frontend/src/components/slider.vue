<template>

  <label class="slider">
    <input type="range" @change="toggle" class="slider-range" v-model.number="item[name]" min="0" max="1" step="0.001">
    <div v-if="name == 'brightness'" class="overlay" :style="{backgroundColor: to_css(item), opacity: 0.10 + 0.65 * item[name], width: item[name] * 100 + '%'}"></div>
    <div class="track" :style="{left: item[name] * 100 + '%'}"></div>

  </label>

</template>

<script>

import abstract from './toggle';

export default {
  name: 'slider',
  props: ['color'],
  extends: abstract,
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="css">

.slider {
  padding:0px;
  margin:0px;
  height:100%;
  position:relative;
}

.slider .track,
.slider .overlay {
    position: absolute;
    width: 100%;
    height: 100%;
    top:0px;
    left:0px;
    pointer-events:none;
}
.slider .track {
  width: 2px;
  right: 0px;
  background: #ddd;
  border-right: 1px solid rgba(255,255,255,0.7);
}

.slider-range {
  width:  100%;
  padding:0px;
  margin: 0px;
  height:100%;
  opacity: 0;

}

</style>