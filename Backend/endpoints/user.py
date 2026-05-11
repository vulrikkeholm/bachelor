from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel
from models.user_model import User, CreateUser, UserLogin, UserResponse, OtpUri
from models.aes_keys_model import AesKeys
from db.session import get_db
from endpoints.auth import generate_otp_uri, secret_key_generator, pwd_context
from main import limiter
from passlib.context import CryptContext
from passlib.hash import argon2
import uuid
import pyotp
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64


router = APIRouter()

ENCRYPTION_ALGORITHM = "AES"
KEY_SIZE = 32  # 256 bits
ITERATION_COUNT = 10000
TAG_LENGTH = 16  # 128 bits

@router.get("/contacts", response_model=List[UserResponse], tags=["Contacts"])
def get_contacts(session: Session = Depends(get_db)):
    try:
        users = session.exec(
            select(User)
        ).all()
        print(users)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signup", response_model=OtpUri, tags=["Users"])
@limiter.limit("5/minute")
def signup(request: Request, create_user: CreateUser, session: Session = Depends(get_db)):
    try:
        statement = select(User).where(User.email == create_user.email)
        existing_user = session.exec(statement).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        secret_key = secret_key_generator()

        totp_uri: str = generate_otp_uri(secret_key, create_user.name)

        user = User(
            email=create_user.email,
            name=create_user.name,
            password=pwd_context.hash(create_user.password),
            otp_secret=secret_key,
            public_key=create_user.public_key,
            encrypted_private_key=create_user.encrypted_private_key,
            encrypted_private_key_salt=create_user.encrypted_private_key_salt,
        )



        aesKeys = AesKeys(
            user_id = user.id,
            aes_key = derive_key()
        )

        otpUri = OtpUri(
            totp_uri=totp_uri
        )



        session.add(user)
        session.add(aesKeys)
        session.commit()
        session.refresh(user)

        return otpUri
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error creating user: {str(e)}")


@router.put("/{id}", tags=["Users"])
def update_user(id: str, new_user: User, session: Session = Depends(get_db)):
    with Session(get_db) as session:
        user_from_db = session.exec(select(User).where(User.id == id)).first()
        updated_user_info = new_user.model.dump(exclude_unset = True)
        user_from_db.sqlmodel_update(updated_user_info)

        session.add(user_from_db)
        session.commit()
        session.refresh(user_from_db)

        return user_from_db


def derive_key():
    password = os.urandom(16).hex()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=os.urandom(16),
        iterations=ITERATION_COUNT
    )
    return kdf.derive(password.encode()).hex()

"""
def get_current_user(session: Session = Depends(get_db)):
    user = session.exec(select(User).where(User.email == user.email)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/me", tags=["Users"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    
    Get the current logged-in user's information.
    Requires authentication via JWT token.
    
    return current_user



@router.get("/chats", response_model = List[chats], tags = ["Chats"])
def get_user_chats(current_user: User = Depends(get_current_user), session: Session = Depends(get_db)):

"""
   
    