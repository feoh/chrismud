from sqlmodel import SQLModel, create_engine, Session
from fastapi import FastAPI
import models

sqlite_file_name='chrismud.db'
sqlite_url='sqlite:///' + sqlite_file_name

engine = create_engine(sqlite_url)

engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.get("/player/create/{player_name}")
def create_player(player_name: str):
    with Session(engine) as session:
        player = models.Player(name=player_name)
        session.add(player)
        session.commit()
