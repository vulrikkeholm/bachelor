from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.aes_keys_model import AesKeysCreate, AesKeys, AesKeysResponseModel as AesKeysResponse
from db.session import get_db
from typing import List
from endpoints.auth import read_jwt_token_from_user
from models.user_model import User


router = APIRouter()

@router.get("/", tags=["keys"])
async def get_aes_key(session: Session = Depends(get_db), current_user: User = Depends(read_jwt_token_from_user)):

    aesKey = session.exec(select(AesKeys).where(AesKeys.user_id == current_user.id)).first()

    if not aesKey:
        raise HTTPException(status_code=404, detail="Key not found")

    return AesKeysResponse(aes_key=aesKey.aes_key)
    
