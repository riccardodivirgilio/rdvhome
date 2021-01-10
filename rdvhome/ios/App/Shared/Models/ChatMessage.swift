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
    var icon: String
    
    var on: Bool
    var ordering: Int
    
    //var hue: Double
    //var brightness: Double
    //var saturation: Double
    
    var allow_on: Bool
    var allow_hue: Bool
}
