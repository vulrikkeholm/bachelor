from sqlmodel import Field, SQLModel
from pydantic import constr
from typing import Optional
import uuid


class User(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    otp_secret: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    admin: Optional[str] = Field(default="False") # acces levels: False for private user and True for administrators
    email: str = Field(default=None, unique=True)
    password: str = Field(default=None)

class CreateUser(SQLModel):
    name: str
    email: str
    password: constr(min_length=8, max_length=128)

class UserLogin(SQLModel):
    email: str
    password: str

