use crate::messages::{Status};
use actix::prelude::*;
use actix::utils::IntervalFunc;
use std::time::Duration;
use serde::{Deserialize, Serialize};

#[derive(Copy, Clone, Debug, Deserialize, Serialize)]
pub struct Switch {
    pub id: &'static str,
    pub name: &'static str,
    pub power: bool,
}

impl Switch {
    fn tick(&mut self, _ctx: &mut Context<Self>) {
        println!("tick {}", self.id);
    }
}

impl Actor for Switch {
    type Context = Context<Self>;

    fn started(&mut self, ctx: &mut Context<Self>) {
      // spawn an interval stream into our context
        IntervalFunc::new(Duration::from_millis(2000), Self::tick)
            .finish()
            .spawn(ctx);
    }
}


impl Handler<Status> for Switch {
    type Result = ();

    fn handle(&mut self, msg: Status, _ctx: &mut Context<Self>) -> Self::Result {
        println!("Status received");
    }
}