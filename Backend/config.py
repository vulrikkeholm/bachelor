from pydantic_settings import BaseSettings
from datetime import timedelta

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:kIrUOnFFulezbePpszmFGnMpYiPQSdlB@centerbeam.proxy.rlwy.net:49068/railway"
    JWT_SECRET_KEY: str = "78d15d862465c5363a30406a8e163dbaabb8a78f330f448542bb99896016ff9f86cb7d97c95df8c1b9490a3c9b2fb3e578b69e0b88af0884d2f06670bd143894"
    JWT_ALGORITHM: str = "HS265"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        case_sensitive = True

settings = Settings() 
