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

func session() -> URLSessionWebSocketTask {
    URLSession.shared.webSocketTask(with: URL(string: "ws://rdvhome.local:8500/websocket")!)
}

class ControlListModel: ObservableObject {
    // Main list view model
    // ObservableObject so that updates are detected
    
    private var webSocketTask: URLSessionWebSocketTask
    @Published var controls = [String: ControlViewModel]()
    
    private var last_message_date = Date()

    init() {
        webSocketTask = session()
    }
    
    func connect() {
        
        webSocketTask.receive(completionHandler: onReceive)
        webSocketTask.resume()
        
        self.send(text:"/switch")
    }
    
    func reconnect() {
        webSocketTask = session()
        connect()
    }
    
    func heartbeat() {
        // The heartbeat is trying to reconnect every second the app is alive
        // The timer is happening only while the app is on screen
        webSocketTask.sendPing() { error in
            if let error = error {
                print("PING ERROR", error)
                self.reconnect()
            }
        }
    }
    

    
    
    private func onReceive(incoming: Result<URLSessionWebSocketTask.Message, Error>) {
        
        if case .success(let message) = incoming {
            webSocketTask.receive(completionHandler: onReceive)
            
            if case .string(let text) = message {
                
                print("INCOMING MSG")
                
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
            print("ABORTING", error)
        }
    }
    
    func send(text: String, debounce: TimeInterval = 0) {
                
        let comp = Date(timeIntervalSinceNow:-debounce)
        let to_skip = comp <= last_message_date
        
        if !to_skip {
            webSocketTask.send(.string(text)) { error in
                if let error = error {
                    print("ERROR SENDING MESSAGE", error)
                }
            }
            last_message_date = Date()
        }
    }
    
    func switch_power(control: ControlViewModel, debounce: TimeInterval = 0) {
        let mode = control.on ? "on" : "off"
        self.send(text:"/switch/\(control.id)/set?mode=\(mode)", debounce:debounce)
    }
    func switch_color(control: ControlViewModel, debounce: TimeInterval = 0) {
        let h = Int(round(100 * control.hue))
        let s = Int(round(100 * control.saturation))
        let b = Int(round(100 * control.brightness))
        self.send(text:"/switch/\(control.id)/set?hue=\(h)&saturation=\(s)&brightness=\(b)", debounce:debounce)
    }
    func switch_random_color(control: ControlViewModel) {
        let hue: Double = control.hue + (Double.random(in: 0..<0.3) + 0.2) * (Int.random(in: 0..<1) == 0 ? -1 : 1)
        
        if hue <= 0 {
            control.hue = 1 - hue
        } else if hue >= 1{
            control.hue = hue - 1
        } else {
            control.hue = hue
        }
        
        control.saturation = Double.random(in: 0.8..<1)
        self.switch_color(control: control)
    }
}
