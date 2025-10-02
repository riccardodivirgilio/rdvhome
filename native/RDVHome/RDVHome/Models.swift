import Foundation
import SwiftUI

#if canImport(UIKit)
import UIKit
#elseif canImport(AppKit)
import AppKit
#endif

struct APIResponse: Codable {
    let mode: String
    let switches: [String: HomeSwitch]
    let status: Int?
    let success: Bool?
    let unixtime: Double?
}

struct HomeSwitch: Codable, Identifiable {
    let id: String
    var name: String?
    var kind: String?
    var icon: String?
    var alias: [String]?
    var ordering: Int?
    var zone: String?
    var allowOn: Bool?
    var allowHue: Bool?
    var allowSaturation: Bool?
    var allowBrightness: Bool?
    var allowDirection: Bool?
    var allowVisibility: Bool?

    // State properties
    var on: Bool?
    var off: Bool?
    var hue: Double?
    var saturation: Double?
    var brightness: Double?
    var up: Bool?
    var down: Bool?

    enum CodingKeys: String, CodingKey {
        case id, name, kind, icon, alias, ordering, zone
        case allowOn = "allow_on"
        case allowHue = "allow_hue"
        case allowSaturation = "allow_saturation"
        case allowBrightness = "allow_brightness"
        case allowDirection = "allow_direction"
        case allowVisibility = "allow_visibility"
        case on, off, hue, saturation, brightness, up, down
    }

    var isOn: Bool {
        return on ?? false
    }

    var color: Color {
        guard let h = hue, let s = saturation, let b = brightness else {
            return .white
        }
        return Color(hue: h, saturation: s, brightness: b)
    }

    var hexColor: String {
        guard let h = hue, let s = saturation, let b = brightness else {
            return "#FFFFFF"
        }

        #if canImport(UIKit)
        let platformColor = UIColor(hue: h, saturation: s, brightness: b, alpha: 1.0)
        #elseif canImport(AppKit)
        let platformColor = NSColor(hue: h, saturation: s, brightness: b, alpha: 1.0)
        #endif

        var r: CGFloat = 0
        var g: CGFloat = 0
        var bl: CGFloat = 0
        var a: CGFloat = 0
        platformColor.getRed(&r, green: &g, blue: &bl, alpha: &a)

        let rgb: Int = (Int)(r*255)<<16 | (Int)(g*255)<<8 | (Int)(bl*255)<<0
        return String(format: "#%06X", rgb)
    }
}
