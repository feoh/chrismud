from sqlmodel import Field, SQLModel
import uuid
from typing import List

class   Player(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    location: uuid.UUID = Field(default=None)
    heard: List[str] = []

