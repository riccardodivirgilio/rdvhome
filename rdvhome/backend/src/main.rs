mod ws;
mod lobby;
use lobby::Lobby;
mod messages;
mod websocket;
use websocket::websocket_view;
use actix::Actor;

use actix_web::{App, HttpServer};

const ADDRESS: &str = "0.0.0.0:8500";

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let chat_server = Lobby::default().start(); //create and spin up a lobby

    println!("Starting server on {}.", ADDRESS);

    HttpServer::new(move || {
        App::new()
            .service(websocket_view) //register our route. rename with "as" import or naming conflict
            .data(chat_server.clone()) //register the lobby
    })
    .bind(ADDRESS)?
    .run()
    .await
}