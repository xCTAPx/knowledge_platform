import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.session import AuthSession
from app.models.user import User

ACCESS_MINUTES = 15
REFRESH_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _cookie_flags() -> dict:
    return {"httponly": True, "samesite": "lax", "secure": settings.app_env == "production"}


def _access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.jwt_secret, algorithm="HS256")


def start_session(response: Response, db: Session, user_id: int, old: AuthSession | None = None) -> None:
    if old:
        db.delete(old)
    raw = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            user_id=user_id,
            token_hash=_token_hash(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS),
        )
    )
    db.commit()
    flags = _cookie_flags()
    response.set_cookie("access_token", _access_token(user_id), max_age=ACCESS_MINUTES * 60, path="/", **flags)
    response.set_cookie(
        "refresh_token", raw, max_age=REFRESH_DAYS * 86400, path="/api/v1/auth", **flags
    )


def clear_session_cookies(response: Response) -> None:
    flags = _cookie_flags()
    response.delete_cookie("access_token", path="/", **flags)
    response.delete_cookie("refresh_token", path="/api/v1/auth", **flags)


def rotate_session(request: Request, response: Response, db: Session) -> None:
    raw = request.cookies.get("refresh_token")
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _token_hash(raw))) if raw else None
    now = datetime.now(timezone.utc)
    if not session or session.expires_at < now:
        if session:
            db.delete(session)
            db.commit()
        clear_session_cookies(response)
        raise HTTPException(401, "Invalid token")
    start_session(response, db, session.user_id, old=session)


def end_session(request: Request, response: Response, db: Session) -> None:
    raw = request.cookies.get("refresh_token")
    if raw:
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _token_hash(raw)))
        if session:
            db.delete(session)
            db.commit()
    clear_session_cookies(response)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        user_id = int(jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Invalid token")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user
