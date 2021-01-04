<template>
    <Page>
        <ActionBar title="Welcome to rdv home"/>
        <ListView for="item in connected_switches">
          <v-template>
            <!-- Shows the list item label in the default color and style. -->
            <DockLayout class="line" stretchLastChild="true" >
              <Label class="icon" :text="item.icon" dock="left" />
              <Switch class="toggle" v-model="item.on" dock="right" @checkedChange="e => toggle_event(e, item)" />
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

require('nativescript-websockets');

export default {
    extends: abstract,
watch: {
    switches: {
    handler:function(newVal) {
      console.log("new Value is " + newVal)
    },
     deep:true
    },

  },
    computed: {
        connected_switches: function() {
            if (this.connected) {
                return values(this.switches)
            }
            return []
        }
    },
    methods: {
        values,
        toggle_event: function(e, item) {

            console.log(e)

            const checked = e.object.checked;

            console.log(`Switch new value ${checked}: ${item.on}`);

            if ((checked == true || checked == false)) {
                

                // this.toggle(item)
            }


        },
        websocket: function(arg) {
            return new WebSocket(arg);
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


