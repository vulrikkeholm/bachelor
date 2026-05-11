from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from models.mess_model import MessageCreate, Message, MessageResponse
from db.session import get_db
from typing import List, Optional
from sockets import sio_server
from endpoints.auth import read_jwt_token_from_user
from models.user_model import User
from main import limiter

router = APIRouter()

@router.post("/", tags = ["messages"])
@limiter.limit("60/minute")
async def send_message(request: Request, data: MessageCreate, session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):

    room_id = "_".join(sorted([str(current_user.id), data.receiver]))

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
            "chat",
            {
                "id": new_msg.id,
                "sender": current_user.id,
                "receiver": data.receiver,
                "text": data.message,
                "room": room_id
            },
            room=room_id
        )
        return {"status": "sent", "id": new_msg.id} 
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error creating message: {str(e)}")


@router.get("/", tags = ["messages"])
async def get_messages(user: str, session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user), after: Optional[int]=None):
    #Der skal tilføjes noget så man kun henter beskeder fra en bestemt chat
    try:
        query = select(Message).where(
            ((Message.sender == current_user.id) & (Message.receiver == user)) |
            ((Message.sender == user) & (Message.receiver == current_user.id))
        )
        if after:
            query = query.where(Message.id > after)
        query = query.order_by(Message.id)
        all_messages = session.exec(query).all()
        return all_messages
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error retrieving message: {str(e)}") 
    
#Deleting messages from DB, after they have been fetched in frontend
@router.delete("/", tags=["messages"])
async def delete_messages(user: str, session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):
    try:
        messages = session.exec(
            select(Message).where(
                #Tjek at den kun sletter beskeder når modtager har hentet dem
                ((Message.sender == current_user.id) & (Message.receiver == user)) |
                ((Message.sender == user) & (Message.receiver == current_user.id))
            )
        ).all()
        for msg in messages:
            session.delete(msg)
        session.commit()
        return {"status": "deleted"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error deleting messages: {str(e)}")
