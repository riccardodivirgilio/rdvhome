#if os(iOS)
import HomeKit
import Combine

private let targetRooms = ["Living", "Studio", "Bedroom", "Windows", "Bathrooms", "Scene"]

@MainActor
class HomeKitManager: NSObject, ObservableObject {
    static let shared = HomeKitManager()

    @Published var homes: [HMHome] = []
    @Published var syncing = false
    @Published var syncLog: [String] = []
    @Published var syncDone = false

    private let manager = HMHomeManager()

    override init() {
        super.init()
        manager.delegate = self
    }

    func sync() {
        guard let home = manager.homes.first else {
            syncLog = ["No HomeKit home found."]
            return
        }

        // Build name→room map from API switches
        let switches = APIService.shared.switches
        var roomAssignment: [String: String] = [:]
        for sw in switches {
            if let name = sw.name, let room = sw.room {
                roomAssignment[name] = room
            }
        }

        guard !roomAssignment.isEmpty else {
            syncLog = ["No switches loaded yet — refresh and try again."]
            return
        }

        syncing = true
        syncDone = false
        syncLog = ["Starting sync…"]

        Task {
            do {
                // 1. Ensure all target rooms exist
                var roomMap: [String: HMRoom] = [:]
                for room in home.rooms {
                    roomMap[room.name] = room
                }
                for name in targetRooms {
                    if roomMap[name] == nil {
                        let room = try await home.addRoom(withName: name)
                        roomMap[name] = room
                        log("Created room: \(name)")
                    }
                }

                // 2. Assign each accessory to its room
                var moved = 0
                for acc in home.accessories {
                    let target = roomAssignment[acc.name] ?? "Scene"
                    guard let targetRoom = roomMap[target] else { continue }
                    let current = home.rooms.first(where: { $0.accessories.contains(where: { $0.uniqueIdentifier == acc.uniqueIdentifier }) })
                    if current?.name == targetRoom.name { continue }
                    try await home.assignAccessory(acc, to: targetRoom)
                    log("→ \(acc.name)  [\(current?.name ?? "Default") → \(targetRoom.name)]")
                    moved += 1
                }

                log("Done. \(moved) accessor\(moved == 1 ? "y" : "ies") moved.")
                syncing = false
                syncDone = true
            } catch {
                log("Error: \(error.localizedDescription)")
                syncing = false
            }
        }
    }

    private func log(_ msg: String) {
        syncLog.append(msg)
    }
}

extension HomeKitManager: HMHomeManagerDelegate {
    func homeManagerDidUpdateHomes(_ manager: HMHomeManager) {
        homes = manager.homes
    }
}

// Async wrappers for HomeKit callback-based APIs
extension HMHome {
    func addRoom(withName name: String) async throws -> HMRoom {
        try await withCheckedThrowingContinuation { cont in
            addRoom(withName: name) { room, error in
                if let error { cont.resume(throwing: error) }
                else if let room { cont.resume(returning: room) }
            }
        }
    }

    func assignAccessory(_ accessory: HMAccessory, to room: HMRoom) async throws {
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            assignAccessory(accessory, to: room) { error in
                if let error { cont.resume(throwing: error) }
                else { cont.resume() }
            }
        }
    }
}
#endif
