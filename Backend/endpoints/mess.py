from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from Backend.models.mess_model import MessageCreate, Message, MessageResponse
from db.session import get_db
from typing import List

router = APIRouter()

#messages = []

@router.post("/", tags = ["messages"])
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



@router.get("/", tags = ["messages"])
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

'''
    for msg in :
        if msg["receiver"] == user:
            user_message.append(msg)

    return user_message


transactions = db.exec(
            select(Transaction).where(
                (Transaction.from_id == current_user.id) | (
                    Transaction.to_id == current_user.id)
            )
        ).all()
'''