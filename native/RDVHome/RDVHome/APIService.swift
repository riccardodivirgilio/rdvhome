import Combine
import Foundation

#if canImport(UIKit)
    import UIKit
#endif

class APIService: ObservableObject {
    static let shared = APIService()

    private let wsURL = "ws://localhost:8500/websocket"
    //private let wsURL = "ws://rdvhome.local:8500/websocket"

    @Published var switches: [HomeSwitch] = []
    @Published var isConnected = false
    @Published var isConnecting = false
    @Published var errorMessage: String?

    private var switchesById: [String: HomeSwitch] = [:]
    private var webSocketTask: URLSessionWebSocketTask?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 3
    private var pingTimer: Timer?
    private var lastMessageTime: Date?
    private var appStateObserver: AnyCancellable?
    private var isReconnecting = false

    private init() {
        setupAppStateObserver()
    }

    private func setupAppStateObserver() {
        #if canImport(UIKit)
            appStateObserver = NotificationCenter.default.publisher(
                for: UIApplication.willEnterForegroundNotification
            )
            .sink { [weak self] _ in
                guard let self = self else { return }
                self.reconnectAttempts = 0
                self.errorMessage = nil
                if !self.isConnected && !self.isConnecting {
                    self.connect()
                } else {
                    self.checkConnection()
                }
            }
        #endif
    }

    func connect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        pingTimer?.invalidate()
        pingTimer = nil

        guard !isReconnecting else {
            print("Already reconnecting, skipping")
            return
        }

        guard reconnectAttempts < maxReconnectAttempts else {
            print("Max reconnection attempts reached")
            DispatchQueue.main.async {
                self.isConnecting = false
                self.errorMessage = "Unable to connect to server"
            }
            return
        }

        guard let url = URL(string: wsURL) else {
            DispatchQueue.main.async {
                self.errorMessage = "Invalid WebSocket URL"
            }
            return
        }

        DispatchQueue.main.async {
            self.isConnecting = true
            self.isConnected = false
            self.errorMessage = nil
        }

        reconnectAttempts += 1
        print(
            "Attempting to connect to WebSocket (attempt \(reconnectAttempts)/\(maxReconnectAttempts))"
        )

        webSocketTask = URLSession.shared.webSocketTask(with: url)
        webSocketTask?.resume()
        receiveMessage()

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            if let task = self.webSocketTask, task.state == .running {
                print("✅ WebSocket connected successfully")
                self.isConnected = true
                self.isConnecting = false
                self.reconnectAttempts = 0
                self.errorMessage = nil
                self.lastMessageTime = Date()
                self.sendMessage("/switch")
                self.setupPingTimer()
            } else {
                print("❌ Failed to establish connection")
                self.handleDisconnection(reason: "Failed to connect")
            }
        }
    }

    func disconnect() {
        print("Disconnecting WebSocket")
        pingTimer?.invalidate()
        pingTimer = nil
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isReconnecting = false
        DispatchQueue.main.async {
            self.isConnected = false
            self.isConnecting = false
        }
    }

    private func setupPingTimer() {
        pingTimer?.invalidate()
        pingTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] _ in
            self?.checkConnection()
        }
    }

    func checkConnection() {
        guard !isReconnecting else { return }
        guard let task = webSocketTask else {
            if isConnected {
                handleDisconnection(reason: "Connection lost")
            }
            return
        }

        if task.state != .running {
            if isConnected {
                handleDisconnection(reason: "Connection closed")
            }
            return
        }

        task.sendPing { [weak self] error in
            if let error = error {
                print("WebSocket ping failed: \(error)")
                self?.handleDisconnection(reason: "Connection timeout")
            }
        }
    }

    private func handleDisconnection(reason: String) {
        guard !isReconnecting else { return }
        print("Disconnected: \(reason)")
        isReconnecting = true

        DispatchQueue.main.async {
            self.isConnected = false
            self.isConnecting = false
        }

        pingTimer?.invalidate()
        pingTimer = nil

        if reconnectAttempts < maxReconnectAttempts {
            print("Will retry connection in 2 seconds...")
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                self.isReconnecting = false
                if !self.isConnected {
                    self.connect()
                }
            }
        } else {
            isReconnecting = false
            DispatchQueue.main.async {
                self.errorMessage = reason
            }
        }
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .success(let message):
                self.lastMessageTime = Date()
                switch message {
                case .string(let text):
                    self.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                self.receiveMessage()
            case .failure(let error):
                print("WebSocket receive error: \(error)")
                self.handleDisconnection(reason: "Connection lost")
            }
        }
    }

    private func handleMessage(_ text: String) {
        print("📥 RAW WEBSOCKET MESSAGE:")
        print(text)
        print("---")

        guard let data = text.data(using: .utf8),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let switchId = json["id"] as? String
        else {
            print("⚠️ Failed to parse JSON or missing 'id' field")
            return
        }

        // Update or create switch in dictionary
        var switchToUpdate = switchesById[switchId] ?? HomeSwitch(id: switchId)

        // Merge fields
        if let name = json["name"] as? String { switchToUpdate.name = name }
        if let kind = json["kind"] as? String { switchToUpdate.kind = kind }
        if let icon = json["icon"] as? String { switchToUpdate.icon = icon }
        if let alias = json["alias"] as? [String] { switchToUpdate.alias = alias }
        if let ordering = json["ordering"] as? Int { switchToUpdate.ordering = ordering }
        if json["zone"] != nil {
            switchToUpdate.zone = json["zone"] as? String
        }
        if let allowOn = json["allow_on"] as? Bool { switchToUpdate.allowOn = allowOn }
        if let allowHue = json["allow_hue"] as? Bool { switchToUpdate.allowHue = allowHue }
        if let allowSaturation = json["allow_saturation"] as? Bool {
            switchToUpdate.allowSaturation = allowSaturation
        }
        if let allowBrightness = json["allow_brightness"] as? Bool {
            switchToUpdate.allowBrightness = allowBrightness
        }
        if let allowDirection = json["allow_direction"] as? Bool {
            switchToUpdate.allowDirection = allowDirection
        }
        if let allowVisibility = json["allow_visibility"] as? Bool {
            switchToUpdate.allowVisibility = allowVisibility
        }
        if let on = json["on"] as? Bool { switchToUpdate.on = on }
        if let off = json["off"] as? Bool { switchToUpdate.off = off }
        if let hue = json["hue"] as? Double { switchToUpdate.hue = hue }
        if let saturation = json["saturation"] as? Double { switchToUpdate.saturation = saturation }
        if let brightness = json["brightness"] as? Double { switchToUpdate.brightness = brightness }
        if let up = json["up"] as? Bool { switchToUpdate.up = up }
        if let down = json["down"] as? Bool { switchToUpdate.down = down }

        switchesById[switchId] = switchToUpdate

        // Update published array
        updateSwitchesArray()
    }

    private func updateSwitchesArray() {
        DispatchQueue.main.async {
            self.switches = self.switchesById.values
                .filter { $0.allowVisibility == true }
                .sorted { ($0.ordering ?? 999) < ($1.ordering ?? 999) }
        }
    }

    private func sendMessage(_ message: String) {
        guard isConnected, let task = webSocketTask, task.state == .running else {
            print("Cannot send message: not connected")
            return
        }
        print("✉️ Send message: \(message)")
        let message = URLSessionWebSocketTask.Message.string(message)
        task.send(message) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }

    func toggleSwitch(id: String, currentState: Bool) {
        let mode = currentState ? "off" : "on"
        let message = "/switch/\(id)/set?mode=\(mode)&hue=-&saturation=-&brightness=-"
        sendMessage(message)
    }

    func setColor(id: String, hue: Double, saturation: Double, brightness: Double) {
        let h = Int(hue * 100)
        let s = Int(saturation * 100)
        let b = Int(brightness * 100)
        let message = "/switch/\(id)/set?hue=\(h)&saturation=\(s)&brightness=\(b)"
        sendMessage(message)
    }

    func setWindowDirection(id: String, direction: String) {
        let message = "/switch/\(id)/set?mode=\(direction)"
        sendMessage(message)
    }

    func stopWindow(id: String) {
        setWindowDirection(id: id, direction: "stop")
    }

    func refresh() {
        if isConnected {
            sendMessage("/switch")
        } else {
            connect()
        }
    }

    func forceReconnect() {
        reconnectAttempts = 0
        errorMessage = nil
        disconnect()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.connect()
        }
    }
}
