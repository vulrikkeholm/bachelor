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

# Returns the current user's own public key
@router.get("/me/public-key", tags=["Keys"])
def get_my_public_key(
    session: Session = Depends(get_db),
    current_user: User = Depends(read_jwt_token_from_user)
):
    if not current_user.public_key:
        raise HTTPException(status_code=404, detail="No public key registered")
    return {"publicKey": current_user.public_key}


# Returns the encrypted private key blob for cross-device restore
@router.get("/me/encrypted-private-key", tags=["Keys"])
def get_encrypted_private_key(
    session: Session = Depends(get_db),
    current_user: User = Depends(read_jwt_token_from_user)
):
    if not current_user.encrypted_private_key:
        raise HTTPException(
            status_code=404,
            detail="No encrypted private key found"
        )

    return current_user.encrypted_private_key