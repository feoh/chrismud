
from sqlmodel import Field, SQLModel
import uuid

class LocationExit(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    location: uuid.UUID
    destination: uuid.UUID
    exit_message: str

