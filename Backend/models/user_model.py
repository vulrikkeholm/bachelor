from sqlmodel import Field, SQLModel
from pydantic import constr

import uuid

class CreateUser(SQLModel):
    name: str = Field(default=None, nullable=False)
    email: str = Field(default=None, nullable=False, unique=True)
    password: constr(min_length=8, max_length=100)

class User(CreateUser, table = True):
    id: uuid.UUID = Field(default_factory = uuid.uuid4, primary_key = True) 
    #username: str = Field(default = None)
    password: str = Field(default=None, nullable=False)

class UserLogin(CreateUser):
    email: str
    password: str

