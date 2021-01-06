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

struct SubmittedChatMessage: Encodable {
	let message: String
}

struct ReceivingChatMessage: Decodable, Identifiable {
	let date: Date
	let id: UUID
	let message: String
}

