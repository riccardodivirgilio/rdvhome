//
//  ChatScreen.swift
//  SwiftChat
//
//  Created by Freek Zijlmans on 15/08/2020.
//

import Combine
import Foundation
import SwiftUI


struct ChatScreen: View {

	@StateObject private var model = ChatScreenModel()
	
	// MARK: - Events
	private func onAppear() {
        
        print("appear")
		model.connect()
	}
	
	private func onDisappear() {
		model.disconnect()
	}

    // MARK: -
    var body: some View {
           NavigationView {
               List(controls) { control in
                   ControlRow(control: control)
               }
           }
       }
}


struct ControlRow: View {
    var control: Control

    var body: some View {
        HStack {

            Text(control.name)

            Spacer()
        }
    }
}

struct ControlRow_Previews: PreviewProvider {
    static var previews: some View {
        ControlRow(control: controls[1])
    }
}


// MARK: - Chat Screen model
/**
 * All business logic is performed in this Observable Object.
 */
private final class ChatScreenModel: ObservableObject {

	
	private var webSocketTask: URLSessionWebSocketTask?
	
	@Published private(set) var messages: [ReceivingChatMessage] = []

	// MARK: - Connection
	func connect() {
        
        let url = URL(string: "ws://127.0.0.1:8500/websocket")!

        print("Connect", url)
        
		guard webSocketTask == nil else {
			return
		}
        

        
        
        
		webSocketTask = URLSession.shared.webSocketTask(with: url)
		webSocketTask?.receive(completionHandler: onReceive)
		webSocketTask?.resume()
	}
	
	func disconnect() {
		webSocketTask?.cancel(with: .normalClosure, reason: nil)
	}
	
	// MARK: - Sending / recieving
	private func onReceive(incoming: Result<URLSessionWebSocketTask.Message, Error>) {
		webSocketTask?.receive(completionHandler: onReceive)

		if case .success(let message) = incoming {
			onMessage(message: message)
		}
		else if case .failure(let error) = incoming {
			print("Error", error)
		}
	}
	
	private func onMessage(message: URLSessionWebSocketTask.Message) {
		if case .string(let text) = message {
			guard let data = text.data(using: .utf8),
				  let chatMessage = try? JSONDecoder().decode(ReceivingChatMessage.self, from: data)
			else {
				return
			}

			DispatchQueue.main.async {
				withAnimation(.spring()) {
					self.messages.append(chatMessage)
				}
			}
		}
	}
	
	func send(text: String) {

		let message = SubmittedChatMessage(message: text)
		guard let json = try? JSONEncoder().encode(message),
			  let jsonString = String(data: json, encoding: .utf8)
		else {
			return
		}
		
		webSocketTask?.send(.string(jsonString)) { error in
			if let error = error {
				print("Error sending message", error)
			}
		}
	}
	
	deinit {
		disconnect()
	}
}
