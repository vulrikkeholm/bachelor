from pydantic_settings import BaseSettings
from datetime import timedelta

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:kIrUOnFFulezbePpszmFGnMpYiPQSdlB@centerbeam.proxy.rlwy.net:49068/railway"
    #JWT_SECRET_KEY: str = ""
    #JWT_ALGORITHM: str = ""
    #RESEND_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        case_sensitive = True

settings = Settings() 
