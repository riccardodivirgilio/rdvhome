//
//  ColorPickerView.swift
//  RdvHome
//
//  Created by Riccardo on 18/01/21.
//

import SwiftUI

struct ColorPickerView: View {
    
    var title : String?
    
    @ObservedObject var control: ControlViewModel
    @ObservedObject var model: ControlListModel
    
    var body: some View {
        ColorPicker(
            title ?? "",
            selection:Binding(
                get: {control.color},
                set: { value in
                    control.color = value
                    model.switch_color(control:control, debounce: 0.20)
                }
            ),
            supportsOpacity:false
        )
    }
}
