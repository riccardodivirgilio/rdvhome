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
                        control.on = v
                        model.switch_power(control:control)
                }
            )
        )
        .disabled(!control.allow_on)
        .toggleStyle(
            SwitchToggleStyle(tint: control.allow_hue ? control.color() : .gray)
        )
    }
}
