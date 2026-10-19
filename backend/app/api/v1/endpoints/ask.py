from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.paging import contains
from app.core.database import get_db
from app.core.llm import complete
from app.core.security import require_auth
from app.core.uploads import UPLOAD_DIR
from app.models.file import File
from app.models.note import Note
from app.models.user import User

router = APIRouter()
MAX_ITEMS = 8
MAX_CHARS = 1500


class AskIn(BaseModel):
    q: str


class AskOut(BaseModel):
    answer: str


def _clip(text: str) -> str:
    text = text.strip()
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS] + "…"


def _file_body(stored: str) -> str:
    path = UPLOAD_DIR / stored
    if path.suffix.lower() not in {".txt", ".md"} or not path.is_file():
        return "Unreadable file extension"
    return _clip(path.read_text(encoding="utf-8", errors="replace"))


@router.post("/ask", response_model=AskOut)
def ask(data: AskIn, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    q = data.q.strip()
    if not q:
        raise HTTPException(400, "Ask a question")
    attached = exists().where(File.note_id == Note.id, contains(File.name, q))
    notes = db.scalars(
        select(Note)
        .where(Note.user_id == user.id, or_(contains(Note.title, q), contains(Note.content, q), attached))
        .options(selectinload(Note.files))
        .order_by(Note.id.desc())
        .limit(MAX_ITEMS)
    ).all()
    files = db.scalars(
        select(File)
        .where(File.user_id == user.id, File.note_id.is_(None), contains(File.name, q))
        .order_by(File.id.desc())
        .limit(MAX_ITEMS)
    ).all()
    if not notes and not files:
        notes = db.scalars(
            select(Note).where(Note.user_id == user.id).options(selectinload(Note.files)).order_by(Note.id.desc()).limit(MAX_ITEMS)
        ).all()
        files = db.scalars(
            select(File).where(File.user_id == user.id, File.note_id.is_(None)).order_by(File.id.desc()).limit(MAX_ITEMS)
        ).all()
    parts = [f"Question: {q}", "Library:"]
    for note in notes:
        names = ", ".join(item.name for item in note.files)
        chunk = f"# {note.title}\n{_clip(note.content)}"
        if names:
            chunk += f"\nAttached: {names}"
            for item in note.files:
                body = _file_body(item.stored)
                if body:
                    chunk += f"\n[{item.name}]\n{body}"
        parts.append(chunk)
    for item in files:
        chunk = f"# File {item.name}"
        body = _file_body(item.stored)
        if body:
            chunk += f"\n{body}"
        parts.append(chunk)
    return AskOut(answer=complete("\n\n".join(parts)))
