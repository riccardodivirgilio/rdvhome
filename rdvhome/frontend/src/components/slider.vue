<template>

<label class="slider">
    <input type="range" class="slider-range" @change="toggle" :value="value" :name="name">
</label>


</template>

<script>
export default {
  name: 'slider',
  props: ['color', 'value'],
  data: function() {
    return {

    }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
.slider {
    width: 100%;
    border:none;
    height: 10px;
    position: relative;
}

.slider-range {
    -webkit-appearance: none;
    width: 100%;
    height: 10px;
    background: #efefef;
    outline: none;
    opacity: 0.7;
    -webkit-transition: .2s;
    transition: opacity .2s;
    margin:0px;
    padding:0px;
    position: relative;
    top:-5px;
}

.slider-range:hover {
    opacity: 1;
}

.slider-range::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 10px;
    background: #ddd;
    cursor: pointer;
}

.slider-range::-moz-range-thumb {
    width: 20px;
    height: 0px;
    background: #ddd;
    cursor: pointer;
}
</style>