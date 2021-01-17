//
//  SliderView.swift
//  SwiftChat
//
//  Created by Riccardo on 17/01/21.
//

import SwiftUI

struct SliderView: View {
    @Binding var value: Double
    
    var processor: (Double) -> Double
    
    var colors: [Color]
    
    var body: some View {
        Slider(
            value: Binding(
                get: {value},
                set: {(v) in value = processor(v)}
            ),
            in: 0...1
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
