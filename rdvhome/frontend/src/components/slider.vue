<template>

  <label class="slider">
    <input type="range"  @change="toggle" class="slider-range" v-model.number="value" :name="name"  min="0" max="1" step="0.01">
    <div class="overlay" v-bind:style="{backgroundColor: color ? color : 'white', opacity: 0.15 * value, width: value * 100 + '%'}"></div>
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
  methods: {
      toggle (e) {
          this.$emit('input', this.value);
      }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss">

$track-color: rgba(0, 0, 0, 0) !default;
$thumb-color: #ddd !default;

$thumb-height: 100% !default;
$thumb-width:  1px !default;

$track-width:  100% !default;
$track-height: 100% !default;

@mixin track {
  cursor: pointer;
  height: $track-height;
  transition: all .2s ease;
  width: $track-width;
}

@mixin thumb {
  background: $thumb-color;
  cursor: pointer;
  height: $thumb-height;
  width:  $thumb-width;
  padding:0px;
  margin: 0px;
}

.slider {
  padding:0px;
  margin:0px;
  height:100%;
  position:relative;
}

.slider .overlay {
    position: absolute;
    width: 100%;
    height: 100%;
    top:0px;
    left:0px;
    pointer-events:none;
}

.slider-range {
  -webkit-appearance: none;
  width:  $track-width;
  padding:0px;
  margin: 0px;
  height:100%;


  &:focus {
    outline: 0;

    &::-webkit-slider-runnable-track {
      background: $track-color;
    }

    &::-ms-fill-lower {
      background: $track-color;
    }

    &::-ms-fill-upper {
      background: $track-color;
    }
  }

  &::-webkit-slider-runnable-track {
    @include track;
    background: $track-color;
  }

  &::-webkit-slider-thumb {
    @include thumb;
    -webkit-appearance: none;
    margin-top: calc(($track-height) / 2) - ($thumb-height / 2);
  }

  &::-moz-range-track {
    @include track;
    background: $track-color;
  }

  &::-moz-range-thumb {
    @include thumb;
  }

  &::-ms-track {
    @include track;
    background: transparent;
    border-color: transparent;
    border-width: ($thumb-height / 2) 0;
    color: transparent;
  }

  &::-ms-fill-lower {
    background: $track-color;
  }

  &::-ms-fill-upper {
    background: $track-color;
  }

  &::-ms-thumb {
    @include thumb;
    margin-top: 0;
  }
}

</style>