//
//  ControlList.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import SwiftUI

struct SingleView: View {
    var title: String?
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    var body: some View {
        HStack {
            if control.on && control.allow_hue {
                ColorPickerView(
                    control: control,
                    model: model
                )
                .frame(width: 30, alignment: .trailing)
            } else {
                Text(control.icon)
                    .frame(width: 30, alignment: .center)
                    
            }
            
            Text(title ?? control.name)
                .lineLimit(1)
            Spacer()
            PowerToggleView(control: control, model: model)
                .frame(width: 1, alignment: .trailing)
        }
        .padding(.top, 4)
        .padding(.bottom, 4)
        .listRowBackground(control.row_background())
        .disabled(!control.allow_on)
        .opacity(control.allow_on ? 1 : 0.5)
    }
}

struct SingleViewWithNavigation: View {
    var title: String?
    
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    var body: some View {
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
                }.buttonStyle(PlainButtonStyle()).frame(width: 0).opacity(0)
            }
        }
        .listRowBackground(control.row_background())
    }
}

struct ControlListView: View {

    var controls: [ControlViewModel]
    @ObservedObject var model: ControlListModel
    
    var current_on_color: [ControlViewModel] {
        controls.filter { c in c.on && c.allow_hue }
    }

    var body: some View {
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

            SingleViewWithNavigation(
                control: ControlViewModel(
                    with: controls.filter { c in c.on && c.allow_on },
                    name: "On",
                    icon: "💡"
                ),
                model: model
            )

            ForEach(controls) {
                control in
                SingleViewWithNavigation(control: control, model: model)
            }
        }
    }
}
