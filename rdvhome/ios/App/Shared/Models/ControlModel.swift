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

class ControlListModel: ObservableObject {
    // Main list view model
    // ObservableObject so that updates are detected
    
    private var webSocketTask: URLSessionWebSocketTask?
    @Published var controls = [String: ControlViewModel]()

    func connect() {
        
        let url = URL(string: "ws://rdvhome.local:8500/websocket")!
        
        print("Connecting", url)
        
        guard webSocketTask == nil else {
            return
        }
        
        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.receive(completionHandler: onReceive)
        webSocketTask?.resume()
        
        self.send(text:"/switch")
    }
    
    private func onReceive(incoming: Result<URLSessionWebSocketTask.Message, Error>) {
        webSocketTask?.receive(completionHandler: onReceive)
        
        if case .success(let message) = incoming {
            if case .string(let text) = message {
                
                print("i got", text)
                
                guard let data = text.data(using: .utf8),
                      let control = try? JSONDecoder().decode(ControlModel.self, from: data)
                else {
                    return
                }
                
                DispatchQueue.main.async {
                    self.controls[control.id] = ControlViewModel(with: control)
                }
            }
        }
        else if case .failure(let error) = incoming {
            print("Error", error)
        }
    }
    
    func send(text: String) {
        webSocketTask?.send(.string(text)) { error in
            if let error = error {
                print("Error sending message", error)
            }
        }
    }
    
    func switch_power(id: String, on: Bool) {
        let mode = on ? "on" : "off"
        self.send(text:"/switch/\(id)/set?mode=\(mode)")
    }
    
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
    
    func color() -> Color {
        return Color(
            hue: hue,
            saturation: saturation,
            brightness: brightness
        )
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
