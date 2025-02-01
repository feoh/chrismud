from sqlmodel import SQLModel, create_engine, Session, select
from fastapi import FastAPI
from models.player import Player
from models.thing import Thing
from models.location import Location

import uuid


def initialize_database():
    sqlite_file_name='chrismud.db'
    sqlite_url='sqlite:///' + sqlite_file_name

    engine = create_engine(sqlite_url, echo=True)

    SQLModel.metadata.create_all(engine)
    return engine

def initialize_world(engine):
    with Session(engine) as session:
        # Create the Limbo location
        player = Player(name="Wizard")
        session.add(player)
        session.commit()

        # Create a thing
        thing = Thing(name="Veeblefetzer")
        session.add(thing)
        session.commit()

        # Create Limbo, the first location!
        limbo = Location(name="Limbo", description="""
                         In the beginning, there was Limbo. It is a dark,
                         """)
        session.add(limbo)
        session.commit()


app = FastAPI()

@app.post("/player/create/{player_name}")
def create_player(player_name: str):
    with Session(engine) as session:
        player = Player(name=player_name)
        session.add(player)
        session.commit()
        return player.id

@app.get("/player/list")
def list_players():
    with Session(engine) as session:
        statement = select(Player)
        players = session.exec(statement)
        return players.all()


@app.delete("/player/delete/{player_id}")
def delete_player(player_id: uuid.UUID):
    with Session(engine) as session:
        player = session.get(Player, player_id)
        session.delete(player)
        session.commit()
        return(player_id)


@app.get("/player/get/{player_id}")
def get_player(player_id: uuid.UUID):
    with Session(engine) as session:
        player = session.get(Player, player_id)
        return player

@app.post("/thing/create/{thing_name}")
def create_thing(thing_name: str):
    with Session(engine) as session:
        thing = Thing(name=thing_name)
        session.add(thing)
        session.commit()
        return thing.id

@app.delete("/thing/delete/{thing_id}")
def delete_thing(thing_id: uuid.UUID):
    with Session(engine) as session:
        thing = session.get(Thing, thing_id)
        session.delete(thing)
        session.commit()
        return(thing_id)

@app.get("/thing/get/{thing_id}")
def get_thing(thing_id: uuid.UUID):
    with Session(engine) as session:
        thing = session.get(Thing, thing_id)
        return thing

@app.get("/thing/list")
def list_things():
    with Session(engine) as session:
        statement = select(Thing)
        things = session.exec(statement)
        return things.all()

@app.post("/location/create/{location_name}/{description}")
def create_location(location_name: str, description: str):
    with Session(engine) as session:
        location = Location(name=location_name, description=description)
        session.add(location)
        session.commit()
        return location.id

@app.delete("/location/delete/{location_id}")
def delete_location(location_id: uuid.UUID):
    with Session(engine) as session:
        location = session.get(Location, location_id)
        session.delete(location)
        session.commit()
        return(location_id)

if __name__ == "__main__":
    engine = initialize_database()
    initialize_world(engine)


