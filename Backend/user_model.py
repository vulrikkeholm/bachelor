from sqlmodel import Field

import uuid

class user_model():
    id: uuid.UUID = Field(default_factory = uuid.uuid4, primary_key = True) 
    username: str = Field(default = None)
    password: str = Field(default=None, nullable=False)
    
