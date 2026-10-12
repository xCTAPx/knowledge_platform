from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_auth
from app.models.note import Note
from app.models.user import User

router = APIRouter()


class NoteIn(BaseModel):
    title: str
    content: str = ""
    tags: list[str] = []


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    tags: list[str]


def _owned(note_id: int, user: User, db: Session) -> Note:
    note = db.get(Note, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(404, "Note not found")
    return note


@router.get("/notes", response_model=list[NoteOut])
def list_notes(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    return db.scalars(select(Note).where(Note.user_id == user.id).order_by(Note.id.desc())).all()


@router.post("/notes", response_model=NoteOut)
def create_note(data: NoteIn, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = Note(user_id=user.id, title=data.title, content=data.content, tags=data.tags)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteIn, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    note.title = data.title
    note.content = data.content
    note.tags = data.tags
    db.commit()
    db.refresh(note)
    return note


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    db.delete(_owned(note_id, user, db))
    db.commit()
