// rdvhome: the lights, windows and scenes of the house behind one http api.
// Rust port of the python app in ../rdvhome, see ../knowledge/RDVHOME-RS.md.

mod cli;
mod color;
mod color_names;
mod device;
mod gpio;
mod hap;
mod home;
mod homekit;
mod json;
mod server;
mod store;
mod switch;

#[tokio::main]
async fn main() {
    cli::main().await
}
