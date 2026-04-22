from sqlmodel import Session, create_engine
import os

#Use 6 when running locally
#engine = create_engine(settings.DATABASE_URL)

# use 9 instead of 6 when pushing to main
engine = create_engine(os.environ.get('DATABASE_URL'))

def get_db():
    with Session(engine) as db:
        yield db
