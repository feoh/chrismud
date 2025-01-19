from sqlmodel import Field, SQLModel
import uuid

class   Player(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    location: str

