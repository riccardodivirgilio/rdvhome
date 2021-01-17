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

    // SwiftUI form with data fields
    // note the autocapitalization and keyboard modifiers

    var body: some View {
        VStack {
            Form {
                Section(header: Text("Power")) {
                    Toggle(control.on ? "ON" : "OFF", isOn: $control.on)
                }
                if control.on && control.allow_hue {
                    Section(header: Text("Hue")) {
                        Slider(
                            value: $control.hue,
                            in: 0...1,
                            onEditingChanged: { editing in
                                print(editing)
                            }
                        )
                        .accentColor(Color(hue: control.hue, saturation: 1, brightness: 1))
                        .background(
                            LinearGradient(
                                gradient: Gradient(
                                    colors: [
                                    
                                        Color(hue: 0 / 360, saturation: 1, brightness: 1),
                                        Color(hue: 60 / 360, saturation: 1, brightness: 1),
                                        Color(hue: 120 / 360, saturation: 1, brightness: 1),
                                        Color(hue: 180 / 360, saturation: 1, brightness: 1),
                                        Color(hue: 240 / 360, saturation: 1, brightness: 1),
                                        Color(hue: 300 / 360, saturation: 1, brightness: 1),
                                        Color(hue: 360 / 360, saturation: 1, brightness: 1),
                                    ]),
                                startPoint: .leading,
                                endPoint: .trailing
                            ))
                    }
                    
                    Section(header: Text("Saturation")) {
                        Slider(
                            value: $control.saturation,
                            in: 0...1,
                            onEditingChanged: { editing in
                                print(editing)
                            }
                        ).accentColor(Color(hue: control.hue, saturation: control.saturation, brightness: 1))
                    }
                    Section(header: Text("Brightness")) {
                        Slider(
                            value: $control.brightness,
                            in: 0...1,
                            onEditingChanged: { editing in
                                print(editing)
                            }
                        ).accentColor(control.color())
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
