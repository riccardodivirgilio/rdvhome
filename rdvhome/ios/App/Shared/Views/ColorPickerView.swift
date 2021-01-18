//
//  ColorPickerView.swift
//  SwiftChat
//
//  Created by Riccardo on 18/01/21.
//

import SwiftUI

struct ColorPickerView: View {
    
    var title = ""
    
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    var body: some View {
        ColorPicker(
            title,
            selection:Binding(
                get: {control.color},
                set: { value in
                    control.color = value
                    model.switch_color(control:control)
                }
            ),
            supportsOpacity:false
        )
    }
}
