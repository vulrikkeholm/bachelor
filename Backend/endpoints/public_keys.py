from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.user_model import User
from db.session import get_db
from endpoints.auth import read_jwt_token_from_user

router = APIRouter()

@router.get("/users/{user_id}/public-key", tags=["Keys"])
def get_public_key(
    user_id: str,
    session: Session = Depends(get_db),
    _: User = Depends(read_jwt_token_from_user)
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.public_key:
        raise HTTPException(status_code=404, detail="No public key registered")
    return {"publicKey": user.public_key}