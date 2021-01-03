<template>
    <Page>
        <ActionBar title="Welcome to rdv home"/>
        <ListView for="item in listOfItems" @itemTap="onItemTap">
          <v-template>
            <!-- Shows the list item label in the default color and style. -->
            <DockLayout class="line" stretchLastChild="true" >
              <Label class="icon" text="💡" dock="left" />
              <Switch class="toggle" checked="true" dock="right"  />
              <Label class="name" :text="item.text" dock="bottom" />
            </DockLayout>
          </v-template>
        </ListView>
    </Page>
</template>

<script >
  export default {
    data() {
      return {
        msg: 'Welcome to RdvHome!',
        listOfItems: [{'text': 'Bedroom light'}, {'text': 'Bedroom led'}]
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


