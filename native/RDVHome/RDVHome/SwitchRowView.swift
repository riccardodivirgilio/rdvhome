import SwiftUI

struct SwitchRowView: View {
    let switchItem: HomeSwitch
    @State private var showColorPicker = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Icon and Name
                HStack(spacing: 12) {
                    Text(switchItem.icon ?? "💡")
                        .font(.title2)

                    VStack(alignment: .leading, spacing: 2) {
                        Text(switchItem.name ?? "Unknown")
                            .font(.headline)

                        Text((switchItem.kind ?? "switch").capitalized)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                // Controls based on capabilities
                if switchItem.allowDirection == true {
                    // Window controls
                    WindowControls(switchItem: switchItem)
                } else if switchItem.allowOn == true {
                    // On/Off toggle
                    Toggle(
                        "",
                        isOn: Binding(
                            get: { switchItem.isOn },
                            set: { _ in
                                APIService.shared.toggleSwitch(
                                    id: switchItem.id,
                                    currentState: switchItem.isOn
                                )
                            }
                        )
                    )
                    .toggleStyle(.switch)
                    .labelsHidden()
                }
            }

            // Color indicator and picker for color-capable switches
            if switchItem.allowHue == true || switchItem.allowSaturation == true
                || switchItem.allowBrightness == true
            {
                HStack(spacing: 12) {
                    // Color preview circle
                    Circle()
                        .fill(switchItem.color)
                        .frame(width: 30, height: 30)
                        .overlay(
                            Circle()
                                .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                        )

                    // Color info
                    VStack(alignment: .leading, spacing: 2) {
                        if let hue = switchItem.hue {
                            Text("Hue: \(Int(hue * 360))°")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        if let brightness = switchItem.brightness {
                            Text("Brightness: \(Int(brightness * 100))%")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Spacer()

                    // Edit color button
                    Button(action: {
                        showColorPicker = true
                    }) {
                        Image(systemName: "paintpalette")
                            .foregroundColor(.blue)
                    }
                    .buttonStyle(.borderless)
                }
                .padding(.top, 4)
            }
        }
        .padding(.vertical, 4)
        .sheet(isPresented: $showColorPicker) {
            ColorPickerView(switchItem: switchItem)
        }
    }
}

struct WindowControls: View {
    let switchItem: HomeSwitch
    @State private var isOperating = false

    var body: some View {
        HStack(spacing: 8) {
            Button(action: {
                isOperating = true
                APIService.shared.setWindowDirection(id: switchItem.id, direction: "up")
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    isOperating = false
                }
            }) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
            }
            .buttonStyle(.borderless)
            .disabled(isOperating)

            Button(action: {
                isOperating = true
                APIService.shared.stopWindow(id: switchItem.id)
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    isOperating = false
                }
            }) {
                Image(systemName: "stop.circle.fill")
                    .font(.title2)
                    .foregroundColor(.orange)
            }
            .buttonStyle(.borderless)
            .disabled(isOperating)

            Button(action: {
                isOperating = true
                APIService.shared.setWindowDirection(id: switchItem.id, direction: "down")
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    isOperating = false
                }
            }) {
                Image(systemName: "arrow.down.circle.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
            }
            .buttonStyle(.borderless)
            .disabled(isOperating)
        }
    }
}
