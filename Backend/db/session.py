from sqlmodel import Session, create_engine
#from config import settings
import os

engine = create_engine(os.environ('DATABASE_URL'))

def get_db():
    with Session(engine) as db:
        yield db
