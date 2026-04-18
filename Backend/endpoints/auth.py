from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from models.user_model import User, CreateUser, UserLogin, OtpVerificationModel
from db.session import get_db
from passlib.context import CryptContext
from passlib.hash import argon2
from datetime import datetime, timedelta, timezone
from config import settings
import pyotp
import qrcode
import jwt
import os

security = HTTPBearer()

router = APIRouter()

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__type="ID",          # Use Argon2id variant
    argon2__time_cost=2,        # 2 iterations
    argon2__memory_cost=47104,  # 47.104 MB
    argon2__parallelism=1       # 1 degree of parallelism
)


def read_jwt_token_from_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db)
) -> User:
    print("CREDENTIALS:", credentials)
    
    """
    decoding token claims:
    (
    sub_id, 
    sub_admin,
    sub_email
    )
    """
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            
            # settings.JWT_SECRET_KEY,
            #os.environ.get('JWT_SECRET_KEY'),
            settings.JWT_SECRET_KEY, 
            # algorithms=settings.JWT_ALGORITHM
            algorithms=[settings.JWT_ALGORITHM]
        )
        print("PAYLOAD:", payload)

        sub_email = payload.get("sub_email")
        sub_admin = payload.get("sub_admin")
        sub_id = payload.get("sub_id")

        if sub_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
    except jwt.ExpiredSignatureError:
        print("TOKEN EXPIRED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    
    except jwt.PyJWTError as e:
        print("JWT ERROR:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = session.exec(select(User).where(User.id == sub_id)).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    elif user.id != sub_id or user.admin != sub_admin:
        raise HTTPException(
            status_code=status.HTTP_418_IM_NOT_A_TEAPOT,
            detail="I'm not a teapot"
        )

    return user


@router.post("/login", tags=["Authentication"])
def login(user_login: UserLogin, session: Session = Depends(get_db)):
    

    # Authenticate user
   
    statement = select(User).where(User.email == user_login.email)
    user = session.exec(statement).first()

    if not user or not pwd_context.verify(user_login.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    session.commit()

    return {"message": "credentials validated. Write OTP from your authenticator app."}


@router.post("/verify-otp", tags=["Authentication"])
def verify_otp_endpoint(otpVerificationModel: OtpVerificationModel, session: Session = Depends(get_db)):

    # Verify OTP for a user
    statement = select(User).where(User.email == otpVerificationModel.email)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "User not found"
        )

    if verify_otp(user.otp_secret, otpVerificationModel.otp):
        
        print("the code is correct!")
        access_token = create_jwt_token({
            "sub_id": user.id,
            "sub_admin": user.admin,
            "sub_email": user.email
            })
        return {"token": access_token, "token_type": "bearer"}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "OTP could not be validated"
            )


"""
code structuring the essential OTP functionalities
"""
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


"""
code structuring the token functionality
"""
def create_jwt_token(data_in_token: dict) -> str:
    token_data_dict = data_in_token.copy()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data_dict.update({"exp": expiration})
    encoded_jwt_token = jwt.encode(
        token_data_dict,
        os.environ.get('JWT_SECRET_KEY')
    )
    return encoded_jwt_token

