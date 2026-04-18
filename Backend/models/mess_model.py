from sqlmodel import SQLModel, Field
from pydantic import BaseModel

class Message(SQLModel, table = True):
    id: int = Field(default=None, primary_key=True)
    sender: str = Field(default=None)
    receiver: str = Field(default=None)
    encrypted_msg: str = Field(default=None)

#Validation models
class MessageCreate(BaseModel):
    receiver: str
    message: str

class MessageResponse(BaseModel):
    sender: str
    receiver: str
    message: str
