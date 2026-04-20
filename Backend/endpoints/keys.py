from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.keys_model import KeysCreate, Keys, KeysResponse
from db.session import get_db
from typing import List
from endpoints.auth import read_jwt_token_from_user
from models.user_model import User

router = APIRouter()

@router.post("/", tags=["keys"])
async def store_aes_key(data: KeysCreate, session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):
    try:
        # Check if key already exists for user
        existing_key = session.exec(select(Keys).where(Keys.user_id == current_user.id)).first()
        if existing_key:
            # Update existing key
            existing_key.aes_key = data.aes_key
            session.add(existing_key)
        else:
            # Create new key
            new_key = Keys(
                user_id=current_user.id,
                aes_key=data.aes_key
            )
            session.add(new_key)
        session.commit()
        return {"status": "key stored"}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error storing key: {str(e)}")

@router.get("/", tags=["keys"])
async def get_aes_key(session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):
    try:
        key = session.exec(select(Keys).where(Keys.user_id == current_user.id)).first()
        if not key:
            raise HTTPException(status_code=404, detail="Key not found")
        return KeysResponse(user_id=key.user_id, aes_key=key.aes_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving key: {str(e)}") 
