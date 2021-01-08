//
//  ChatScreen.swift
//  SwiftChat
//
//  Created by Freek Zijlmans on 15/08/2020.
//

import Combine
import Foundation
import SwiftUI



struct Control: Decodable, Hashable, Identifiable {
    var id: String
    var name: String
    var allow_on: Bool
    var on: Bool
}


struct ChatScreen: View {

	@StateObject private var model = ChatScreenModel()
    @State var controls: [Control] = [
        Control(id: "living_1", name: "Living Room", allow_on: true, on: false),
        Control(id: "living_2", name: "Living Room 1", allow_on: true, on: false),
        Control(id: "living_3", name: "Living Room 2", allow_on: true, on: false),
        Control(id: "living_4", name: "Living Room 3", allow_on: true, on: false)
    ]
    
    // MARK: -
    var body: some View {
           NavigationView {
            List(controls.indices) { i in
                    HStack {
                        Text("⚠️")
                        Text(self.$controls[i].wrappedValue.name)
                        Toggle("", isOn:
                            Binding(
                                get: {self.$controls[i].wrappedValue.on},
                                set: {
                                    (v) in self.$controls[i].wrappedValue.on = v
                                    print(v)
                                })
                        )
                    }
               }
           }
           .navigationTitle("RdvHome")
           .onAppear(perform: {model.connect()})
           .onDisappear(perform: {model.disconnect()})
       }
}




// MARK: - Chat Screen model
/**
 * All business logic is performed in this Observable Object.
 */
private final class ChatScreenModel: ObservableObject {

	private var webSocketTask: URLSessionWebSocketTask?
    
	// MARK: - Connection
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
	
	func disconnect() {
		webSocketTask?.cancel(with: .normalClosure, reason: nil)
	}
	
	// MARK: - Sending / recieving
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
                
                print(control)
                
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
	
	deinit {
		disconnect()
	}
}
