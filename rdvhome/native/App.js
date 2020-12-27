import React from 'react';
import { SectionList, StyleSheet, Text, View, Switch } from 'react-native';

import switches from './src/data/switches'
import map       from 'rfuncs/functions/map'
import values       from 'rfuncs/functions/values'
import filter       from 'rfuncs/functions/filter'


const styles = StyleSheet.create({
  container: {
   flex: 1,
   paddingTop: 22
  },
  sectionHeader: {
    paddingTop: 20,
    paddingLeft: 10,
    paddingRight: 10,
    paddingBottom: 2,
    fontSize: 14,
    fontWeight: 'bold',
    backgroundColor: 'rgba(247,247,247,1.0)',
  },
  item: {
    padding: 10,
    fontSize: 18,
    height: 44,
  },
})

const SectionListBasics = () => {
    return (
      <View style={styles.container}>
        <SectionList
          sections={[
            {title: 'Lights', data: map(
              s => <View><Switch/><Text>{s.icon + ' ' + s.name}</Text></View>,
              filter(
                s => s.allow_visibility,
                values(switches)
              )
            )},
          ]}
          renderItem={({item}) => <Text style={styles.item}>{item}</Text>}
          renderSectionHeader={({section}) => <Text style={styles.sectionHeader}>{section.title}</Text>}
          keyExtractor={(item, index) => index}
        />
      </View>
    );
}

export default SectionListBasics;