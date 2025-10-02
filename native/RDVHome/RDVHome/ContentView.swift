import SwiftUI

struct ContentView: View {
    @StateObject private var apiService = APIService.shared
    @Environment(\.scenePhase) private var scenePhase
    @State private var selectedZoneId: String = "all"

    var zones: [String] {
        let allZones = apiService.switches.compactMap { $0.zone }
        return Array(Set(allZones)).sorted()
    }

    var filteredSwitches: [HomeSwitch] {
        guard selectedZoneId != "all" else {
            return apiService.switches
        }
        return apiService.switches.filter { $0.zone == selectedZoneId }
    }

    var body: some View {
        NavigationSplitView {
            // Sidebar
            SidebarView(zones: zones, selectedZoneId: $selectedZoneId)
        } detail: {
            // Detail view
            SwitchListView(
                switches: filteredSwitches,
                selectedZone: selectedZoneId == "all" ? nil : selectedZoneId
            )
        }
        .toolbar(id: "main") {
            ToolbarItem(id: "status", placement: .status) {
                HStack(spacing: 6) {
                    Circle()
                        .fill(apiService.isConnected ? Color.green : (apiService.isConnecting ? Color.yellow : Color.red))
                        .frame(width: 8, height: 8)

                    if apiService.isConnecting {
                        Text("Connecting")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else if !apiService.isConnected {
                        Text("Disconnected")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }

            ToolbarItem(id: "refresh", placement: .automatic) {
                Button(action: {
                    apiService.refresh()
                }) {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(!apiService.isConnected)
                .help("Refresh switches")
            }
        }
        .onAppear {
            if !apiService.isConnected && !apiService.isConnecting {
                apiService.connect()
            }
        }
        .onChange(of: scenePhase) { oldPhase, newPhase in
            if newPhase == .active {
                apiService.checkConnection()
            }
        }
    }
}

struct ZoneItem: Identifiable, Hashable {
    let id: String
    let displayName: String
}

struct SidebarView: View {
    let zones: [String]
    @Binding var selectedZoneId: String

    var zoneItems: [ZoneItem] {
        var items = [ZoneItem(id: "all", displayName: "All")]
        items += zones.map { ZoneItem(id: $0, displayName: $0) }
        return items
    }

    var body: some View {
        List(selection: $selectedZoneId) {
            Section("Zones") {
                ForEach(zoneItems) { item in
                    Text(item.displayName)
                        .tag(item.id)
                }
            }
        }
        .navigationTitle("Zones")
        #if os(macOS)
        .navigationSplitViewColumnWidth(min: 180, ideal: 200, max: 250)
        #endif
    }
}

struct SwitchListView: View {
    @StateObject private var apiService = APIService.shared
    let switches: [HomeSwitch]
    let selectedZone: String?

    var body: some View {
        Group {
            if apiService.isConnecting || (!apiService.isConnected && switches.isEmpty) {
                // Initial connection state
                VStack(spacing: 20) {
                    ProgressView()
                        .scaleEffect(1.5)

                    Text(apiService.isConnecting ? "Connecting..." : "Disconnected")
                        .font(.headline)

                    if let error = apiService.errorMessage {
                        Text(error)
                            .foregroundColor(.red)
                            .multilineTextAlignment(.center)
                            .padding()
                            .font(.subheadline)
                    }

                    if !apiService.isConnecting {
                        Button("Try Again") {
                            apiService.forceReconnect()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                VStack(spacing: 0) {
                    // Connection status banner (only shown when disconnected but have cached data)
                    if !apiService.isConnected {
                        HStack {
                            Image(systemName: "wifi.slash")
                                .foregroundColor(.white)
                            Text("Connection Lost")
                                .font(.subheadline)
                                .foregroundColor(.white)
                            Spacer()
                            Button("Reconnect") {
                                apiService.forceReconnect()
                            }
                            .font(.caption)
                            .foregroundColor(.white)
                            .buttonStyle(.borderless)
                        }
                        .padding(.horizontal)
                        .padding(.vertical, 12)
                        .background(Color.red)
                    }

                    if switches.isEmpty {
                        ContentUnavailableView {
                            Label("No Switches", systemImage: "lightbulb.slash")
                        } description: {
                            if let zone = selectedZone {
                                Text("No switches found in \(zone)")
                            } else {
                                Text("No switches available")
                            }
                        }
                    } else {
                        List {
                            ForEach(switches) { switchItem in
                                SwitchRowView(switchItem: switchItem)
                            }
                        }
                        .disabled(!apiService.isConnected)
                        .opacity(apiService.isConnected ? 1.0 : 0.6)
                    }
                }
            }
        }
        .navigationTitle(selectedZone ?? "All Switches")
    }
}

#Preview {
    ContentView()
}
