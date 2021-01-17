//
//  ControlDetailView.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import SwiftUI

struct ControlDetailView: View {
    // Data passed from parent list view
    @ObservedObject var control: ControlViewModel

    // SwiftUI form with data fields
    // note the autocapitalization and keyboard modifiers

    var body: some View {
        VStack {
            Form {
                Section(header: Text("Name")) {
                    TextField("Enter first name", text: $control.name)
                        .autocapitalization(.words)
                }
                Section(header: Text("Icon")) {
                    TextField("Enter last name", text: $control.icon)
                        .autocapitalization(.words)
                }
            }
            Text("Registered on:")
                .font(.headline)
                .padding(6)
            Text("\(control.id)")
        }
    }
}
