from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import MessageCreate

router = APIRouter()

messages = []

@router.post("/messages")
def send_message(data: MessageCreate):
    msg = {
        "sender": data.sender,
        "receiver": data.receiver,
        "message": data.message
    }
    
    messages.append(msg)

    return {"status": "sent"} 


@router.get("/messages")
def get_messages(user):

    user_message = []

    for msg in messages:
        if msg["receiver"] == user:
            user_message.append(msg)

    return user_message