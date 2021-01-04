<template>
    <Page>
        <ActionBar title="Welcome to rdv home"/>
        <ListView for="item in connected_switches">
          <v-template>
            <!-- Shows the list item label in the default color and style. -->
            <DockLayout class="line" stretchLastChild="true" >
              <Label class="icon" :text="item.icon" dock="left" />
              <Switch class="toggle" :checked="item.on" dock="right" @checkedChange="e => toggle_event(e, item.id)" v-if="item.allow_on"/>
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
import filter   from 'rfuncs/functions/filter'
import sort_by  from 'rfuncs/functions/sort_by'

require('nativescript-websockets');

export default {
    extends: abstract,
    computed: {
        connected_switches: function() {
            if (this.connected) {
                return sort_by(
                    filter(
                        s => s.allow_visibility,
                        values(this.switches)
                    ),
                    s => s.ordering
                )
            }
            return []
        }
    },
    methods: {
        values,
        toggle_event: function(e, id) {
            const checked = e.object.checked;
            const on = this.switches[id].on
            if ((checked == true || checked == false) && checked != on) {
                this.switches[id].on = checked
                this.toggle(this.switches[id])
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


