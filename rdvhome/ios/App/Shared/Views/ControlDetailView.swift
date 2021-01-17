//
//  ControlDetailView.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import SwiftUI



struct SliderView: View {
    @Binding var control: Double
    @ObservedObject var model: ControlListModel
    
    var colors: [Color]
    
    var body: some View {
        Slider(
            value: $control,
            in: 0...1,
            onEditingChanged: { editing in
                print(editing)
            }
        )
        .accentColor(.white)
        .padding(.top, 10)
        .padding(.bottom, 10)
        .listRowBackground(
            LinearGradient(
                gradient: Gradient(colors: colors),
                startPoint: UnitPoint(x:0.08, y:0.5),
                endPoint: UnitPoint(x:0.92, y:0.5)
            )
        )
    }
}


struct ControlDetailView: View {
    // Data passed from parent list view
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    // SwiftUI form with data fields
    // note the autocapitalization and keyboard modifiers

    var body: some View {
        VStack {
            List {
                Section(header: Text("Power")) {
                    PowerToggleView(control: control, model:model, title:control.on ? "ON" : "OFF")
                        .padding(.top, 4)
                        .padding(.bottom, 4)
                }
                if control.on && control.allow_hue {
                    Section(header: Text("Color")) {
                        SliderView(control: $control.hue, model: model, colors: [
                            Color(hue: 0 / 360, saturation: 1, brightness: 1),
                            Color(hue: 60 / 360, saturation: 1, brightness: 1),
                            Color(hue: 120 / 360, saturation: 1, brightness: 1),
                            Color(hue: 180 / 360, saturation: 1, brightness: 1),
                            Color(hue: 240 / 360, saturation: 1, brightness: 1),
                            Color(hue: 300 / 360, saturation: 1, brightness: 1),
                            Color(hue: 360 / 360, saturation: 1, brightness: 1),
                        ])
                        SliderView(control: $control.saturation, model: model, colors: [
                            Color(hue: control.hue, saturation: 0, brightness: 1),
                            Color(hue: control.hue, saturation: 1, brightness: 1)
                        ])
                        SliderView(control: $control.brightness, model: model, colors: [
                            Color(hue: control.hue, saturation: control.saturation, brightness: 0),
                            Color(hue: control.hue, saturation: control.saturation, brightness: 1)
                        ])
                    }
                }
            }
            
            Text("Registered on:")
                .font(.headline)
                .padding(6)
                
            Text("\(control.id)")
                .padding(6)
        }
        .navigationBarTitle(control.name)
        
    }
}
