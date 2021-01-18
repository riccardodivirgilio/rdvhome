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
        print("sending", text)
        webSocketTask?.send(.string(text)) { error in
            if let error = error {
                print("Error sending message", error)
            }
        }
    }
    
    func switch_power(control: ControlViewModel) {
        let mode = control.on ? "on" : "off"
        self.send(text:"/switch/\(control.id)/set?mode=\(mode)")
    }
    func switch_hue(control: ControlViewModel) {
        let value = Int(round(100 * control.hue))
        self.send(text:"/switch/\(control.id)/set?hue=\(value)")
    }
    func switch_saturation(control: ControlViewModel) {
        let value = Int(round(100 * control.saturation))
        self.send(text:"/switch/\(control.id)/set?saturation=\(value)")
    }
    func switch_brightness(control: ControlViewModel) {
        let value = Int(round(100 * control.brightness))
        self.send(text:"/switch/\(control.id)/set?brightness=\(value)")
    }
    
    func heartbeat() {
        print("ping")
        webSocketTask?.sendPing() { error in
            if let error = error {
                print("Error sending ping", error)
                
                self.connect()
            }
        }

        
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
    
    func row_background() -> Color {
        return color().opacity(on ? 0.3 : 0)
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
