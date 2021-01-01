use crate::messages::{ClientActorMessage, Connect, Disconnect, WsMessage};
use actix::prelude::{Actor, Context, Handler, Recipient};
use std::collections::{HashMap};
use uuid::Uuid;


type Socket = Recipient<WsMessage>;

pub struct Lobby {
    sessions: HashMap<Uuid, Socket>, //self id to self
}

impl Default for Lobby {
    fn default() -> Lobby {
        Lobby {
            sessions: HashMap::new(),
        }
    }
}

impl Lobby {
    fn send_message(&self, message: &str, id_to: &Uuid) {
        if let Some(socket_recipient) = self.sessions.get(id_to) {
            let _ = socket_recipient
                .do_send(WsMessage(message.to_owned()));
        } else {
            println!("attempting to send message but couldn't find user id.");
        }
    }
}

impl Actor for Lobby {
    type Context = Context<Self>;
}

impl Handler<Disconnect> for Lobby {
    type Result = ();

    fn handle(&mut self, msg: Disconnect, _: &mut Context<Self>) {
        if self.sessions.remove(&msg.id).is_some() {

        }
    }
}

impl Handler<Connect> for Lobby {
    type Result = ();

    fn handle(&mut self, msg: Connect, _: &mut Context<Self>) -> Self::Result {

        self.sessions.insert(
            msg.self_id,
            msg.addr,
        );

        self.send_message(&format!("your id is {}", msg.self_id), &msg.self_id);
    }
}

impl Handler<ClientActorMessage> for Lobby {
    type Result = ();

    fn handle(&mut self, msg: ClientActorMessage, _ctx: &mut Context<Self>) -> Self::Result {
        self.sessions.iter().for_each(|(id, _)| self.send_message(&msg.msg, id));
    }
}