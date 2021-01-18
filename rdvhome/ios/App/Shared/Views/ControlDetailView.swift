//
//  ControlDetailView.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import SwiftUI








struct ControlDetailView: View {
    // Data passed from parent list view
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    // SwiftUI form with data fields
    // note the autocapitalization and keyboard modifiers

    var body: some View {
        VStack {
            List {
                SingleView(title:control.on ? "ON" : "OFF", control: control, model: model)
                    .listRowBackground(control.row_background())
                if control.on && control.allow_hue {
                    Section(header: Text("Color")) {
                        SliderView(
                            value: $control.hue,
                            control: control,
                            model: model,
                            colors: [
                                Color(hue: 0 / 360, saturation: 1, brightness: 1),
                                Color(hue: 60 / 360, saturation: 1, brightness: 1),
                                Color(hue: 120 / 360, saturation: 1, brightness: 1),
                                Color(hue: 180 / 360, saturation: 1, brightness: 1),
                                Color(hue: 240 / 360, saturation: 1, brightness: 1),
                                Color(hue: 300 / 360, saturation: 1, brightness: 1),
                                Color(hue: 360 / 360, saturation: 1, brightness: 1),
                            ])
                        SliderView(
                            value: $control.saturation,
                            control: control,
                            model: model,
                            colors: [
                                Color(hue: control.hue, saturation: 0, brightness: 1),
                                Color(hue: control.hue, saturation: 1, brightness: 1)
                            ])
                        SliderView(
                            value: $control.brightness,
                            control: control,
                            model: model,
                            colors: [
                                Color(hue: control.hue, saturation: control.saturation, brightness: 0),
                                Color(hue: control.hue, saturation: control.saturation, brightness: 1)
                            ])
                    }
                }
            }
            
            Button(action: {
                control.hue = Double.random(in: 0..<1)
                model.switch_color(control: control)
            }, label: {
                HStack {
                    Spacer()
                    Text("Random Color")
                    Spacer()
                }
            })
            
        }
        .navigationBarTitle(control.name)
    }
}
