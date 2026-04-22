from sqlmodel import Session, create_engine
import os

engine = create_engine(os.environ.get('DATABASE_URL'))

def get_db():
    with Session(engine) as db:
        yield db
