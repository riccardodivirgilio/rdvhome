mod ws;
mod lobby;
mod messages;
mod websocket;
mod switches;
mod home;

use lobby::Lobby;
use websocket::websocket_view;
use actix::Actor;
use actix_web::{App, HttpServer};

const ADDRESS: &str = "0.0.0.0:8500";

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let lobby = Lobby::default().start(); //create and spin up a lobby

    println!("Starting server on {}.", ADDRESS);

    HttpServer::new(move || {
        App::new()
            .service(websocket_view) //register our route. rename with "as" import or naming conflict
            .data(lobby.clone()) //register the lobby
    })
    .bind(ADDRESS)?
    .run()
    .await
}