from fastapi import FastAPI, Depends, HTTPException

from db.base import create_db_and_tables
from endpoints import user, auth, mess

from db.session import get_db
from models.user_model import User
from sqlmodel import Session, select

app = FastAPI()

app.include_router(user.router, prefix="/users")
app.include_router(auth.router, prefix="/auth")
app.include_router(mess.router, prefix="/messages")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()