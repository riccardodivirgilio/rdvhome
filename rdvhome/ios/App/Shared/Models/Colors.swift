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




struct RGB {
    var red: Double
    var green: Double
    var blue: Double
}


struct HSB {
    var hue: Double
    var brightness: Double
    var saturation: Double
}


extension Color {
    
    var rgb: (RGB) {

        typealias NativeColor = UIColor

        var r: CGFloat = 0
        var g: CGFloat = 0
        var b: CGFloat = 0
        var o: CGFloat = 0

        guard NativeColor(self).getRed(&r, green: &g, blue: &b, alpha: &o) else {
            // You can handle the failure here as you want
            return RGB(red:0, green:0, blue: 0)
        }

        return RGB(red:Double(r), green:Double(g), blue:Double(b))
    }
    
    var hsb: (HSB) {
    
        let r = rgb.red
        let g = rgb.green
        let b = rgb.blue
        
        let Max:Double = max(r, g, b)
        let Min:Double = min(r, g, b)

        //h 0-360
        var h:Double = 0
        if Max == Min {
            h = 0.0
        } else if Max == r && g >= b {
            h = 60 * (g-b)/(Max-Min)
        } else if Max == r && g < b {
            h = 60 * (g-b)/(Max-Min) + 360
        } else if Max == g {
            h = 60 * (b-r)/(Max-Min) + 120
        } else if Max == b {
            h = 60 * (r-g)/(Max-Min) + 240
        }
        
        //s 0-1
        var s:Double = 0
        if Max == 0 {
            s = 0
        } else {
            s = (Max - Min)/Max
        }
        
        //v
        let v:Double = Max
                
        return HSB(hue: h / 360, brightness: v, saturation: s)
    }
    
}

