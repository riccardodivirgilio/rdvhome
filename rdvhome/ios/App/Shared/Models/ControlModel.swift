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
        
        send(text: "/switch")
    }
    
    func reconnect() {
        webSocketTask = session()
        connect()
    }
    
    func heartbeat() {
        // The heartbeat is trying to reconnect every second the app is alive
        // The timer is happening only while the app is on screen
        webSocketTask.sendPing { error in
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
    
    func send(text: String, debounce: TimeInterval? = nil) {
        return send(text: [text], debounce: debounce)
    }
    
    func send(text: [String], debounce: TimeInterval? = nil) {
        var to_skip = false
        if let debounce = debounce {
            to_skip = Date(timeIntervalSinceNow: -debounce) <= last_message_date
        }
        if !to_skip {
            webSocketTask.send(.string(text.joined(separator: "\n"))) { error in
                if let error = error {
                    print("ERROR SENDING MESSAGE", error)
                }
            }
            last_message_date = Date()
        }
    }
    
    func switch_power(control: [ControlViewModel], debounce: TimeInterval? = nil) {
        send(text: control.map {
            c in
            let mode = c.on ? "on" : "off"
            return "/switch/\(c.id)/set?mode=\(mode)"
        },
        debounce: debounce)
    }

    func switch_power(control: ControlViewModel, debounce: TimeInterval? = nil) {
        return switch_power(control: [control], debounce: debounce)
    }
    
    func switch_color(control: [ControlViewModel], debounce: TimeInterval? = nil) {
        send(text: control.map { c in
            
            let h = Int(round(100 * c.hue))
            let s = Int(round(100 * c.saturation))
            let b = Int(round(100 * c.brightness))
            
            return "/switch/\(c.id)/set?hue=\(h)&saturation=\(s)&brightness=\(b)"
            
        }, debounce: debounce)
    }

    func switch_color(control: ControlViewModel, debounce: TimeInterval? = nil) {
        return switch_color(control: [control], debounce: debounce)
    }
}
