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
        print("ping", Date())
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
                
                print("INCOMING", text)
                
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
    
    func send(text: String) {
        print("sending", text)
        webSocketTask.send(.string(text)) { error in
            if let error = error {
                print("ERROR SENDING MESSAGE", error)
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

}
