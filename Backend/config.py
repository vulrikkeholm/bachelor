from pydantic_settings import BaseSettings
from datetime import timedelta
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get('DATABASE_URL')
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY')
    JWT_ALGORITHM: str = os.environ.get('JWT_ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        case_sensitive = True

settings = Settings() 
