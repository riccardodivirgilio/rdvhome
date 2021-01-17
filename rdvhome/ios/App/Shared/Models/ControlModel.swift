//
//  ControlsModel.swift
//  DataFlow
//
//  Created by Sarah Reichelt on 14/09/2019.
//  Copyright © 2019 TrozWare. All rights reserved.
//

import Foundation

class ControlListModel: ObservableObject {
    // Main list view model
    // ObservableObject so that updates are detected
    

    @Published var controls: [ControlViewModel] = []

    func fetchData() {
        // avoid too many calls to the API
        if controls.count > 0 { return }

        let address = "https://next.json-generator.com/api/json/get/VyQroKB8P?indent=2"
        guard let url = URL(string: address) else {
            fatalError("Bad data URL!")
        }

        URLSession.shared.dataTask(with: url) { (data, response, error) in
            guard let data = data, error == nil else {
                print("Error fetching data")
                return
            }

            do {
                let jsonDecoder = JSONDecoder()
                jsonDecoder.dateDecodingStrategy = .iso8601
                let dataArray = try jsonDecoder.decode([ControlModel].self, from: data)
                DispatchQueue.main.async {
                    self.controls = dataArray.map { ControlViewModel(with: $0) }.sorted() {
                        $0.last + $0.first < $1.last + $1.first
                    }
                }
            } catch {
                print(error)
            }
        }.resume()
    }

    func refreshData() {
        controls = []
        fetchData()
    }
}

class ControlViewModel: Identifiable, ObservableObject {
    // Main model for use as ObservableObject
    // Derived from JSON via basic model

    // Even though this is not observed directly,
    // it must be an ObservableObject for the data flow to work

    var id = UUID()
    @Published var first: String = ""
    @Published var last: String = ""
    @Published var phone: String = ""
    @Published var address: String = ""
    @Published var city: String = ""
    @Published var state: String = ""
    @Published var zip: String = ""
    @Published var registered: Date = Date()

    init(with control: ControlModel) {
        self.id = control.id
        self.first = control.first
        self.last = control.last
        self.phone = control.phone
        self.address = control.address
        self.city = control.city
        self.state = control.state
        self.zip = control.zip
        self.registered = control.registered
    }
}

struct ControlModel: Codable {
    // Basic model for decoding from JSON

    let id: UUID
    let first: String
    let last: String
    let phone: String
    let address: String
    let city: String
    let state: String
    let zip: String
    let registered: Date

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        id = try values.decode(UUID.self, forKey: .id)
        first = try values.decode(String.self, forKey: .first)
        last = try values.decode(String.self, forKey: .last)
        phone = try values.decode(String.self, forKey: .phone)
        registered = try values.decode(Date.self, forKey: .registered)

        // split up address into separate lines for easier editing
        let addressData = try values.decode(String.self, forKey: .address)
        let addressComponents = addressData.components(separatedBy: ", ")
        address = addressComponents[0]
        city = addressComponents[1]
        state = addressComponents[2]
        zip = addressComponents[3]
    }
}

// Previewing requires using .constant to convert the data to a binding
// Sample data is generated in an extension in Preview Content

extension ControlViewModel {
    // Sample data for use in Previews only

    static func sampleControl() -> ControlViewModel {
        let json = """
        {
          "id": "07534800-9c07-4857-b931-d6541ff0df08",
          "first": "Beasley",
          "last": "Burnett",
          "phone": "+1 (957) 453-3538",
          "address": "740 Jodie Court, Manchester, Vermont, 8934",
          "registered": "2018-06-08T01:08:31+00:00"
        }
        """

        let jsonDecoder = JSONDecoder()
        jsonDecoder.dateDecodingStrategy = .iso8601

        // Uisng force un-wrapping for sample data only, not for production
        let control = try! jsonDecoder.decode(ControlModel.self, from: json.data(using: .utf8)!)
        return ControlViewModel(with: control)
    }
}
