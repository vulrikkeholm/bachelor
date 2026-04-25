from pydantic_settings import BaseSettings
from datetime import timedelta

class Settings(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        case_sensitive = True

settings = Settings() 
