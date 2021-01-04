<template>
    <Page>
        <ActionBar title="Welcome to rdv home"/>
        <ListView for="item in values(switches)">
          <v-template>
            <!-- Shows the list item label in the default color and style. -->
            <DockLayout class="line" stretchLastChild="true" >
              <Label class="icon" :text="item.icon" dock="left" />
              <Switch class="toggle" checked="true" dock="right"  />
              <Label class="name" :text="item.name" dock="bottom" />            
            </DockLayout>
          </v-template>
        </ListView>
    </Page>
</template>

<script >

import abstract from 'frontend/components/app'
import switches from 'frontend/data/switches'
import values   from 'rfuncs/functions/values'
import ws from 'nativescript-websockets'

export default {
    extends: abstract,
    methods: {
        values,
          websocket: function(arg) {
            return new ws(arg, {protocols: ['chat', 'video'], timeout: 100, allowCellular: true});
          }
    }
}
</script>

<style scoped>
    .icon,
    .name {
        height: 60;
    }
    .icon {
        width: 60;
        text-align: center;

    }
    .name {
        text-align: left;
        width: auto;
    }
    .toggle {
        margin-right: 10;
        vertical-align: center;

    }
</style>


