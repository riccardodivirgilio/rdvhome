//
//  ControlList.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import SwiftUI




struct SingleView: View {
    
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    var body: some View {
        HStack {
            Text(control.icon)
            Text(control.name)
            Spacer()
            PowerToggleView(control: control, model: model)
        }
    }
}

struct ControlListView: View {
    // Using an ObservedObject for reference-based data (classes)
    @ObservedObject var model = ControlListModel()
    
    var body: some View {
        NavigationView {
            List {
                // To make the navigation link edits return to here,
                // the data sent must be a direct reference to an element
                // of the ObservedObject, not the closure parameter.
                
                // Thanks to Stewart Lynch (@StewartLynch) for suggesting using a function to
                // get a binding to the control so it coud be passed to the detail view.
                
                // And now thanks to Vadim Shpakovski (@vadimshpakovski) for another option
                // which does not rely on creating a binding to every control, but uses
                // onReceive to react to changes to the control and trigger an update of model.
                // This will be faster for longer lists and feels more like how ObservedObject is meant to be used.
                // Note that ControlDetailView has changed from using @Binding to @ObservedObject.

                ForEach(model.controls.values.sorted(by: {c1, c2 in c1.ordering < c2.ordering})) { control in
                    
                    
                    
                    
                    ZStack {
                        SingleView(control: control, model: model)
                        
                        if control.on && control.allow_hue {
                            NavigationLink(destination:
                                ControlDetailView(control: control, model: model)
                                    .onReceive(control.objectWillChange) { _ in
                                        self.model.objectWillChange.send()
                                    }
                            ) {
                                EmptyView()
                                    
                            }.buttonStyle(PlainButtonStyle()).frame(width:0).opacity(0)
                            
                        }
                        

                    }
                    .listRowBackground(control.row_background())
                    
                    
                }

            }
                
            // This runs when the view appears to load the initial data
            .onAppear(perform: { self.model.connect() })
            
            // set up the navigation bar details
            // EditButton() is a standard View
            .navigationBarTitle("RdvHome")
            /*.navigationBarItems(trailing:
                HStack {
                    Button(action: { self.model.refreshData() }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    Spacer().frame(width: 30)
                    EditButton()
                }
            )*/
        }
    }
}

// To preview this with navigation, it must be embedded in a NavigationView
// but the main ContentView provides the main NavigationView
// so this view will only get its own when in Proview mode

struct ControlList_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            ControlListView()
        }
    }
}

