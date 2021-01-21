//
//  ControlTabView.swift
//  SwiftChat
//
//  Created by Riccardo on 21/01/21.
//

import SwiftUI

struct Room: Identifiable {
    var id: String
    var filter: (ControlViewModel) -> Bool
    var icon: String
}

struct ControlTabView: View {
    
    // Using an ObservedObject for reference-based data (classes)
    @ObservedObject var model = ControlListModel()
    @State private var selection = "Day"
    
    private var rooms: [Room] = [
        Room(
            id: "Day",
            filter: {c in c.alias.contains("living")},
            icon: "house"
        ),
        Room(
            id: "Night",
            filter: {c in c.alias.contains("bedroom") || c.alias.contains("bathroom") || c.alias.contains("studio")},
            icon: "bed.double"
        ),
        Room(
            id: "Scenes",
            filter: {c in c.alias.contains("control") || c.alias.contains("window")},
            icon: "desktopcomputer"
        ),
    ]
        
    var controls: [ControlViewModel] {
        model.controls.values.sorted(by: { c1, c2 in c1.ordering < c2.ordering })
    }
    
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    
    var body: some View {
        NavigationView {
            if controls.isEmpty {
                ProgressView()
            } else {
                TabView(selection: $selection) {
                    ForEach(rooms) {
                        room in
                        ControlListView(
                            controls:controls.filter(room.filter),
                            model:model
                        )
                        .tag(room.id)
                        .tabItem {
                            Image(systemName: room.icon)
                        }
                    }
                }
                .tabViewStyle(PageTabViewStyle())
                .navigationBarTitle("\(selection)")
                .toolbar {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button {
                            let room = rooms.filter({r in r.id == selection}).first!
                            let control = controls.filter(room.filter)
                            for c in control {
                                c.set_random_color()
                            }
                            model.switch_color(control: control)
                            
                        } label: {
                            Image(systemName: "shuffle")
                        }
                        .disabled(controls.isEmpty)
                    }
                }
            }
        }
        // This runs when the view appears to load the initial data
        .onAppear(perform: { self.model.connect() })
        .onReceive(timer) { _ in self.model.heartbeat() }
    }
}
