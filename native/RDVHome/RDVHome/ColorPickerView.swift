import SwiftUI

struct ColorPickerView: View {
    let switchItem: HomeSwitch
    @State private var selectedHue: Double
    @State private var selectedSaturation: Double
    @State private var selectedBrightness: Double
    @State private var isUpdating = false
    @Environment(\.dismiss) var dismiss

    init(switchItem: HomeSwitch) {
        self.switchItem = switchItem
        _selectedHue = State(initialValue: switchItem.hue ?? 0.0)
        _selectedSaturation = State(initialValue: switchItem.saturation ?? 1.0)
        _selectedBrightness = State(initialValue: switchItem.brightness ?? 1.0)
    }

    var selectedColor: Color {
        Color(hue: selectedHue, saturation: selectedSaturation, brightness: selectedBrightness)
    }

    var body: some View {
        NavigationView {
            Form {
                Section {
                    VStack(spacing: 20) {
                        // Color Preview
                        RoundedRectangle(cornerRadius: 12)
                            .fill(selectedColor)
                            .frame(height: 100)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                            )

                        // Hue Slider
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Hue")
                                    .font(.subheadline)
                                Spacer()
                                Text("\(Int(selectedHue * 360))°")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }

                            Slider(value: $selectedHue, in: 0...1)
                                .accentColor(
                                    Color(hue: selectedHue, saturation: 1.0, brightness: 1.0))
                        }

                        // Saturation Slider
                        if switchItem.allowSaturation == true {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text("Saturation")
                                        .font(.subheadline)
                                    Spacer()
                                    Text("\(Int(selectedSaturation * 100))%")
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }

                                Slider(value: $selectedSaturation, in: 0...1)
                                    .accentColor(selectedColor)
                            }
                        }

                        // Brightness Slider
                        if switchItem.allowBrightness == true {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text("Brightness")
                                        .font(.subheadline)
                                    Spacer()
                                    Text("\(Int(selectedBrightness * 100))%")
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }

                                Slider(value: $selectedBrightness, in: 0...1)
                                    .accentColor(selectedColor)
                            }
                        }
                    }
                    .padding(.vertical, 8)
                }

                Section {
                    Button(action: {
                        isUpdating = true
                        APIService.shared.setColor(
                            id: switchItem.id,
                            hue: selectedHue,
                            saturation: selectedSaturation,
                            brightness: selectedBrightness
                        )
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                            isUpdating = false
                            dismiss()
                        }
                    }) {
                        HStack {
                            Spacer()
                            if isUpdating {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle())
                            } else {
                                Text("Apply Color")
                                    .fontWeight(.semibold)
                            }
                            Spacer()
                        }
                    }
                    .disabled(isUpdating)
                }
            }
            .navigationTitle(switchItem.name ?? "Color Picker")
            #if !os(macOS)
                .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                #if os(macOS)
                    ToolbarItem(placement: .automatic) {
                        Button("Done") {
                            APIService.shared.setColor(
                                id: switchItem.id,
                                hue: selectedHue,
                                saturation: selectedSaturation,
                                brightness: selectedBrightness
                            )
                            dismiss()
                        }
                    }
                #else
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Done") {
                            APIService.shared.setColor(
                                id: switchItem.id,
                                hue: selectedHue,
                                saturation: selectedSaturation,
                                brightness: selectedBrightness
                            )
                            dismiss()
                        }
                    }
                #endif
            }
        }
    }
}
