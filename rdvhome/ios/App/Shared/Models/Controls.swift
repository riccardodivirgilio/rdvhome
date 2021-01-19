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
    
    init(with controls: [ControlViewModel], name: String, icon: String, ordering: Int = 0) {
        self.id = controls.map({c in c.id}).joined(separator: "~")
        self.name = name
        self.icon = icon
        self.ordering = ordering
        self.allow_on = !controls.filter({c in c.allow_on}).isEmpty
        self.allow_hue = !controls.filter({c in c.allow_hue}).isEmpty
        self.on = !controls.filter({c in c.on}).isEmpty
        
        if controls.count > 0 {
                        
            self.color = Color(
                red:   controls.map({c in c.color.rgb.red}).reduce(0.0, +) / Double(controls.count),
                green: controls.map({c in c.color.rgb.green}).reduce(0.0, +) / Double(controls.count),
                blue:  controls.map({c in c.color.rgb.blue}).reduce(0.0, +) / Double(controls.count)
            )
                        

        } else {
            self.hue = 0
            self.brightness = 0
            self.saturation = 0
        }
    }
}
