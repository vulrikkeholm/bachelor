from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from db.session import get_db
from models.user_model import User
from endpoints.auth import read_jwt_token_from_user
from typing import List
import json

router = APIRouter()

class PublicKeyUpload(BaseModel):
    publicKey: List[int]

# Save current user's public key
@router.post("/users/public-key", tags=["keys"])
async def save_public_key(
    body: PublicKeyUpload,
    session: Session = Depends(get_db),
    current_user: User = Depends(read_jwt_token_from_user)
):
    current_user.public_key = json.dumps(body.publicKey)
    session.add(current_user)
    session.commit()
    return { "success": True }

# Fetch another user's public key
@router.get("/users/{user_id}/public-key", tags=["keys"])
async def get_public_key(
    user_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(read_jwt_token_from_user)
):
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user or not user.public_key:
        raise HTTPException(status_code=404, detail="Public key not found")

    return { "publicKey": json.loads(user.public_key) }

class RatchetKeyUpload(BaseModel):
    receiver: str
    publicKey: List[int]

# Save ratchet public key (to be picked up by the other peer)
@router.post("/ratchet-key", tags=["keys"])
async def save_ratchet_key(
    body: RatchetKeyUpload,
    session: Session = Depends(get_db),
    current_user: User = Depends(read_jwt_token_from_user)
):
    # Store the ratchet key on the current user's record
    current_user.ratchet_key = json.dumps(body.publicKey)
    session.add(current_user)
    session.commit()
    return { "success": True }

# Fetch another user's ratchet public key
@router.get("/ratchet-key/{user_id}", tags=["keys"])
async def get_ratchet_key(
    user_id: str,
    session: Session = Depends(get_db),
    current_user: User = Depends(read_jwt_token_from_user)
):
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user or not user.ratchet_key:
        raise HTTPException(status_code=404, detail="Ratchet key not found")

    return { "publicKey": json.loads(user.ratchet_key) }