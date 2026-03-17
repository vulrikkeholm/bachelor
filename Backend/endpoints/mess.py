from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.mess_modul import MessageCreate, Message, MessageResponse
from db.session import get_db
from typing import List

router = APIRouter()

#messages = []

@router.post("/messages", tags = ["messages"])
def send_message(data: MessageCreate, session: Session = Depends(get_db)):
    try:
        new_msg = Message(
            sender= data.sender,
            receiver= data.receiver,
            encrypted_msg= data.message
        )
    
        #messages.append(new_msg)

        session.add(new_msg)
        session.commit()
        session.refresh(new_msg)

        return {"status": "sent"} 
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error creating message: {str(e)}")



@router.get("/messages", tags = ["messages"])
def get_messages(user: str, session: Session = Depends(get_db) ):

    #user_message = []
    try:
        all_messages = session.exec(select(Message).where(Message.receiver == user)).all()
        print(all_messages)

        return all_messages

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error retrieving message: {str(e)}") 
