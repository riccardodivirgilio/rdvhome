//
//  ControlsModel.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import Foundation

import CoreLocation
import SwiftUI

struct ControlModel: Codable {
    // Basic model for decoding from JSON

    var id: String
    var name: String
    var alias: Set<String>
    var icon: String
    var ordering: Int
    var allow_on: Bool
    var allow_direction: Bool
    var allow_hue: Bool
    var on: Bool
    var up: Bool
    var down: Bool
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
    @Published var alias: Set<String> = []
    @Published var icon: String = "💡"
    @Published var ordering: Int = 1000
    @Published var allow_on: Bool = false
    @Published var allow_hue: Bool = false
    @Published var allow_direction: Bool = false
    @Published var on: Bool = false
    @Published var up: Bool = false
    @Published var down: Bool = false
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
    
    func set_random_color() {
        let hue: Double = self.hue + (Double.random(in: 0..<0.3) + 0.2) * (Int.random(in: 0..<1) == 0 ? -1 : 1)
        
        if hue <= 0 {
            self.hue = 1 - hue
        } else if hue >= 1 {
            self.hue = hue - 1
        } else {
            self.hue = hue
        }
        
        saturation = Double.random(in: 0.8..<1)
    }
    
    init(with control: ControlModel) {
        self.id = control.id
        self.name = control.name
        self.alias = control.alias
        self.icon = control.icon
        self.ordering = control.ordering
        self.allow_on = control.allow_on
        self.allow_hue = control.allow_hue
        self.allow_direction = control.allow_direction
        self.on = control.on
        self.up = control.up
        self.down = control.down
        self.hue = control.hue
        self.brightness = control.brightness
        self.saturation = control.saturation
    }
    
    init(with controls: [ControlViewModel], name: String = "", icon: String = "", ordering: Int = 0) {
        self.id = controls.map { c in c.id }.joined(separator: "~")
        self.name = name
        self.alias = []
        self.icon = icon
        self.ordering = ordering
        self.allow_on = !controls.filter { c in c.allow_on }.isEmpty
        self.allow_hue = !controls.filter { c in c.allow_hue }.isEmpty
        self.allow_direction = !controls.filter { c in c.allow_direction }.isEmpty
        self.on = !controls.filter { c in c.on }.isEmpty
        self.up = !controls.filter { c in c.up }.isEmpty
        self.down = !controls.filter { c in c.down }.isEmpty
        
        if controls.count > 0 {
            self.color = Color(
                red: controls.map { c in c.color.rgb.red }.reduce(0.0, +) / Double(controls.count),
                green: controls.map { c in c.color.rgb.green }.reduce(0.0, +) / Double(controls.count),
                blue: controls.map { c in c.color.rgb.blue }.reduce(0.0, +) / Double(controls.count)
            )
                        
        } else {
            self.hue = 0
            self.brightness = 0
            self.saturation = 0
        }
    }
}
