//
//  ChatMessage.swift
//  SwiftChat
//
//  Created by Freek Zijlmans on 15/08/2020.
//

import Foundation
import Foundation
import SwiftUI
import CoreLocation

struct Control: Decodable, Hashable, Identifiable {
    var id: String
    var name: String
    var icon: String = "💡"
    
    var ordering: Int = 1000
    
    var allow_on: Bool = false
    var allow_hue: Bool = false
    
    var on: Bool = false
    var hue: Double = 0
    var brightness: Double = 0
    var saturation: Double = 0
    
}
