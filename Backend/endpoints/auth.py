from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from models.user_model import User, CreateUser, UserLogin
from db.session import get_db
from passlib.context import CryptContext
from passlib.hash import argon2
from datetime import datetime, timedelta
from config import settings
import pyotp
import qrcode


router = APIRouter()
pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__type="ID",          # Use Argon2id variant
    argon2__time_cost=2,        # 2 iterations
    argon2__memory_cost=47104,  # 46 MB
    argon2__parallelism=1       # 1 degree of parallelism
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


@router.post("/verify-otp", tags=["otp-verification"])
def verify_otp_endpoint(otp: str, id: str, session: Session = Depends(get_db)):

    """
    Verify OTP for a user
    """

    statement = select(User).where(User.id == id)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if verify_otp(user.otp_secret, otp):
        return {"message": "OTP is valid"}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP"
        )


def generate_otp_uri(secret_key: str, name: str) -> str:
    totp = pyotp.TOTP(secret_key)
    uri = totp.provisioning_uri(name, issuer_name="SMaaS")
    
    QR_code = qrcode.make(uri)
    QR_code.save("totp.png")

    return uri

def secret_key_generator() -> str:
    return pyotp.random_base32()

def verify_otp(secret_key: str, otp: str) -> bool:
    totp = pyotp.TOTP(secret_key)
    return totp.verify(otp)
