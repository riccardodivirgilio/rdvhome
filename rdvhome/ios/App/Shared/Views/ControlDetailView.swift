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
                Section(header: Text("First Name")) {
                    TextField("Enter first name", text: $control.first)
                        .autocapitalization(.words)
                }
                Section(header: Text("Last Name")) {
                    TextField("Enter last name", text: $control.last)
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




struct ControlDetailView_Previews: PreviewProvider {
    static var previews: some View {
        let control = ControlViewModel.sampleControl()
        return ControlDetailView(control: control)
    }
}
