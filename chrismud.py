from sqlmodel import SQLModel, create_engine, Session, select
from fastapi import FastAPI
from models.player import Player
from models.thing import Thing
import uuid

sqlite_file_name='chrismud.db'
sqlite_url='sqlite:///' + sqlite_file_name

engine = create_engine(sqlite_url)

engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.get("/player/create/{player_name}")
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


@app.get("/player/delete/{player_id}")
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

@app.get("/thing/create/{thing_name}")
def create_thing(thing_name: str):
    with Session(engine) as session:
        thing = Thing(name=thing_name)
        session.add(thing)
        session.commit()
        return thing.id

@app.get("/thing/delete/{thing_id}")
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
