//
//  ControlsModel.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import Foundation

import SwiftUI
import CoreLocation

struct ControlModel: Codable {
    // Basic model for decoding from JSON

    var id: String
    var name: String
    var icon: String
    var ordering: Int
    var allow_on: Bool
    var allow_hue: Bool
    var on: Bool
    
    var hue: Double
    var brightness: Double
    var saturation: Double

}


class ControlViewModel: Identifiable, ObservableObject {
    // Main model for use as ObservableObject
    // Derived from JSON via basic model

    // Even though this is not observed directly,
    // it must be an ObservableObject for the data flow to work

    var id: String
    @Published var name: String
    @Published var icon: String = "💡"
    @Published var ordering: Int = 1000
    @Published var allow_on: Bool = false
    @Published var allow_hue: Bool = false
    @Published var on: Bool = false
    @Published var hue: Double = 0
    @Published var brightness: Double = 0
    @Published var saturation: Double = 0
    
    var color: Color {
        get {
            Color(
                hue: hue,
                saturation: saturation,
                brightness: brightness
            )
        }
        set(c) {
            hue = c.hsb.hue
            saturation = c.hsb.saturation
            brightness = c.hsb.brightness
        }
    }
    
    func row_background() -> Color {
        return color.opacity(on ? (allow_hue ? 0.3 : 0.15) : 0)
    }
    
    init(with control: ControlModel) {
        self.id = control.id
        self.name = control.name
        self.icon = control.icon
        self.ordering = control.ordering
        self.allow_on = control.allow_on
        self.allow_hue = control.allow_hue
        self.on = control.on
        self.hue = control.hue
        self.brightness = control.brightness
        self.saturation = control.saturation
    }
    
}
