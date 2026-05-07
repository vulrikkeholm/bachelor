from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from config import settings

class AesKeys(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(default=None)
    aes_key: str = Field(default=None)

#Validation models
class AesKeysCreate(BaseModel):
    user_id: str
    aes_key: str

class AesKeysResponseModel(BaseModel):
    aes_key: str