from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from models.user_model import User, CreateUser
from db.session import get_db
from endpoints.auth import pwd_context

router = APIRouter()

@router.post("/signup", tags=["Users"])
def signup(create_user: CreateUser, session: Session = Depends(get_db)):

    #Create new user and add it to the database

    try:
        statement = select(User).where(User.email == create_user.email)
        existing_user = session.exec(statement).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        user = User(
            email=create_user.email,
            name=create_user.name,
            password=pwd_context.hash(create_user.password)
        )

        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error creating user: {str(e)}")


"""
@router.get("/me", tags=["Users"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    
    Get the current logged-in user's information.
    Requires authentication via JWT token.
    
    return current_user



@router.get("/chats", response_model = List[chats], tags = ["Chats"])
def get_user_chats(current_user: User = Depends(get_current_user), session: Session = Depends(get_db)):

"""
    