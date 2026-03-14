from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class Message(table = True):
    id: int = Field(default=None, primary_key=True)
    sender: int = Field(default=None, foreign_key="user.id")
    receiver: int = Field(default=None, foreign_key="user.id")
    encrypted_msg: str = Field(default=None)

#Validation models
class MessageCreate(BaseModel):
    sender: str
    receiver: str
    message: str

class MessageResponse(BaseModel):
    sender: str
    receiver: str
    message: str
