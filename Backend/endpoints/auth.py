from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from models.user import User, UserCreate, UserResponse, UserLogin
from db.session import get_db
from passlib.context import CryptContext
from passlib.hash import argon2
from datetime import datetime, timedelta
import jwt
from config import settings
import random

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__type="ID",        # Use Argon2id variant
    argon2__time_cost=2,      # 2 iterations
    argon2__memory_cost=47104,  # 46 MB
    argon2__parallelism=1     # 1 degree of parallelism
)

@router.post("/login", tags=["Authentication"])
def login(user_login: UserLogin, session: Session = Depends(get_db)):
    """
    Authenticate user
    """
    statement = select(User).where(User.email == user_login.email)
    user = session.exec(statement).first()

    if not user or not pwd_context.verify(user_login.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    session.commit()

    return {"message": "Login successful"}


