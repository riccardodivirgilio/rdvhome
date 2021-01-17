//
//  SwitchScreen.swift
//  SwiftChat
//
//  Created by Riccardo Di Virgilio
//

import Combine
import Foundation
import SwiftUI

struct SingleView: View {
    
    var control: Control
    var switch_power: (Control, Bool) -> ()
    
    var body: some View {
        HStack {
            Text(control.icon)
            Text(control.name)
            Spacer()
            Toggle("", isOn:
                Binding(
                    get: {control.on},
                    set: {(v) in switch_power(control, v)}
                )
            )
            .opacity(control.allow_on ? 1 : 0)
            .toggleStyle(
                SwitchToggleStyle(tint: control.allow_hue ? control.color : .gray)
            )
        }
        .listRowBackground(control.color.opacity(control.on ? 0.1 : 0))
    }
}

struct SwitchScreen: View {
    
    @StateObject private var model = SwitchScreenModel()
    
    var body: some View {
        NavigationView {
            List {
                ForEach(model.controls.values.sorted(by: {c1, c2 in c1.ordering < c2.ordering})) { control in
                    SingleView(
                        control: control,
                        switch_power: model.switch_power
                    )
                }
            }
            .navigationTitle("RdvHome")
            
            
        }
        .onAppear(perform: {model.connect()})
        .onDisappear(perform: {model.disconnect()})
    }
}

private final class SwitchScreenModel: ObservableObject {
    
    private var webSocketTask: URLSessionWebSocketTask?
    
    @Published private(set) var controls = [String: Control]()
    
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
                      let control = try? JSONDecoder().decode(Control.self, from: data)
                else {
                    return
                }
                
                
                DispatchQueue.main.async {
                    self.controls[control.id] = control
                }
                
                print(control)

            }
        }
        else if case .failure(let error) = incoming {
            print("Error", error)
        }
    }
    
    func switch_power(control: Control, on: Bool) {
        if var c = self.controls[control.id] {
            if c.allow_on {
                c.on = on
                self.controls[control.id] = c
                let mode = on ? "on" : "off"
                self.send(text:"/switch/\(c.id)/set?mode=\(mode)")
            }
        }
    }

    func send(text: String) {
        webSocketTask?.send(.string(text)) { error in
            if let error = error {
                print("Error sending message", error)
            }
        }
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
    }
    
    deinit {
        disconnect()
    }
}
