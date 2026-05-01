from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.mess_model import MessageCreate, Message, MessageResponse
from db.session import get_db
from typing import List
from sockets import sio_server
from endpoints.auth import read_jwt_token_from_user
from models.user_model import User

router = APIRouter()

@router.post("/", tags = ["messages"])
async def send_message(data: MessageCreate, session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):
    try:
        new_msg = Message(
            sender= current_user.id,
            receiver= data.receiver,
            encrypted_msg= data.message
        )
    
        session.add(new_msg)
        session.commit()
        session.refresh(new_msg)
        #For at gøre beskeder real time
        await sio_server.emit(
            "new_message",
            {
                "sender": current_user.id,
                "receiver": data.receiver,
                "message": data.message
            },
            room=data.receiver
        )
        return {"status": "sent"} 
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error creating message: {str(e)}")


@router.get("/", tags = ["messages"])
async def get_messages(user: str, session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):
    #Der skal tilføjes noget så man kun henter beskeder fra en bestemt chat
    try:
        all_messages = session.exec(
            select(Message).where(
                ((Message.sender == current_user.id) & (Message.receiver == user)) |
                ((Message.sender == user) & (Message.receiver == current_user.id))
                ).order_by(Message.id)
        ).all()
        print(all_messages)
        return all_messages
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error retrieving message: {str(e)}") 