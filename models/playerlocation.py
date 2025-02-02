from sqlmodel import Field, SQLModel
import uuid

class PlayerLocation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    player: uuid.UUID = Field(unique=True)
    location: uuid.UUID = Field(unique=True)
    description: str = "A Non descript player."

