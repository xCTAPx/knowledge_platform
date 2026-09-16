import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    end_session,
    get_current_user,
    hash_password,
    rotate_session,
    start_session,
)
from app.models.user import User

router = APIRouter(prefix="/auth")


class UserIn(BaseModel):
    nickname: str
    email: str
    password: str
    age: int | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nickname: str
    email: str
    age: int | None


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: UserIn, response: Response, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(
        nickname=data.nickname,
        email=email,
        hashed_password=hash_password(data.password),
        age=data.age,
    )
    db.add(user)
    db.commit()
    start_session(response, db, user.id)


@router.post("/login")
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not bcrypt.checkpw(data.password.encode(), user.hashed_password.encode()):
        raise HTTPException(401, "Invalid email or password")
    start_session(response, db, user.id)


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    rotate_session(request, response, db)


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    end_session(request, response, db)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
