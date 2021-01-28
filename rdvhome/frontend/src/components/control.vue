<template>

  <a :id="item.id" class="list-item" :class="{on: item.on, off: item.off}" :style="{order: item.ordering}">
    <div class="line" :style="{backgroundColor: hsl_to_css({hue: item.allow_hue ? item.hue : 1, saturation: item.allow_saturation ? 1 : 0, lightness: item.on ? 'var(--lightness-high)' : 'var(--lightness)'})}">
      <btn :item="item" name='advanced_options' :disabled="item.off || ! item.allow_hue">
        <div v-if="item.advanced_options && item.on && item.allow_hue" style="padding-top:3px">&times;</div>
        <div v-else>{{ item.icon }}</div>
      </btn>
      <slider v-if="item.on && item.allow_brightness" :item="item" name='brightness' :onchange="backend.toggle_hsb"/>
      <div class="title">{{ item.name }} </div>
      <div class="controls">
        <updown :item="item" :onchange="backend.toggle_direction" v-if='item.allow_direction' name='up'/>
        <updown :item="item" :onchange="backend.toggle_direction" v-if='item.allow_direction' name='down'/>
        <toggle :item="item" :onchange="backend.toggle" v-if='item.allow_on' name='on'/>
      </div>
    </div>
    <div v-if="item.on && item.advanced_options && item.allow_hue" class="line slider-hue">
      <slider :item="item" name='hue' :onchange="backend.toggle_hsb"/>
    </div>
    <div v-if="item.on && item.advanced_options && item.allow_saturation" class="line slider-saturation" :style="{background:
      'linear-gradient(to right, white 0%, '+hsl_to_css({hue: item.hue, saturation: 1, lightness:1})+' 100%)'}">
      <slider :item="item" name='saturation' :onchange="backend.toggle_hsb"/>
    </div>
  </a>

</template>

<script>

import toggle    from '@/components/toggle';
import btn       from '@/components/btn';
import slider    from '@/components/slider';
import updown    from '@/components/updown';

import {hsl_to_css} from '@/utils/color';


export default {
  name: 'item',
  props: ['item', 'backend'],
  methods: {hsl_to_css},
  components: {
    toggle,
    slider,
    updown,
    btn,
  },

}
</script>
