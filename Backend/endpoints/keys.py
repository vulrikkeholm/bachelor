from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.keys_model import KeysCreate, Keys, KeysResponse
from db.session import get_db
from typing import List
from endpoints.auth import read_jwt_token_from_user
from models.user_model import User
from secrets import token_bytes

router = APIRouter()

@router.get("/", tags=["keys"])
async def get_aes_key(session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):
    try:
        key = session.exec(select(Keys).where(Keys.user_id == current_user.id)).first()
        if not key:
            raise HTTPException(status_code=404, detail="Key not found")
        return KeysResponse(user_id=key.user_id, aes_key=key.aes_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving key: {str(e)}")
