from sqlmodel import SQLModel
from db.session import engine
from models.mess_model import Message


def delete_messages_table():
    print("Dropping messages table...")
    Message.__table__.drop(engine)
    print("Messages table has been dropped successfully!")

if __name__ == "__main__":
    delete_messages_table()
