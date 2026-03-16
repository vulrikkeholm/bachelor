from sqlmodel import Field, SQLModel
from pydantic import constr

import uuid


class CreateUser(SQLModel):
    name: str = Field(default=None, nullable=False)
    email: str = Field(default=None, nullable=False, unique=True)
    password: constr(min_length=8, max_length=100)
    id: str = Field( primary_key = True)

class User(CreateUser, table = True):
    #username: str = Field(default = None)
    #password: str = Field(default=None, nullable=False)
    print(f"hello developers")

class UserLogin(CreateUser):
    email: str
    password: str

#class UserWithID(CreateUser):
