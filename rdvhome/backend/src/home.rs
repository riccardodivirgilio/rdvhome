use crate::switches::Switch;

pub fn generate_switches() -> Vec<Switch> {
    return vec![
        Switch {
            id: "bedroom_light",
            name: "Bedroom light",
            power: true,
        },
        Switch {
            id: "bedroom_led",
            name: "Bedroom led",
            power: true,
        }
    ]
}