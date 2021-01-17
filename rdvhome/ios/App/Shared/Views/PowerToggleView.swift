//
//  PowerToggleView.swift
//  SwiftChat
//
//  Created by Riccardo on 17/01/21.
//

import SwiftUI

struct PowerToggleView: View {
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel

    var title: String = ""
    
    var body: some View {
        Toggle(title, isOn:
            Binding(
                get: {control.on},
                set: {
                    (v) in
                        model.switch_power(id:control.id, on:v)
                        control.on = v
                }
            )
        )
        .disabled(!control.allow_on)
        .toggleStyle(
            SwitchToggleStyle(tint: control.allow_hue ? control.color() : .gray)
        )
    }
}
