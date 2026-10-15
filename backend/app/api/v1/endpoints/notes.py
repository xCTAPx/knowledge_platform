from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.endpoints.files import FileOut
from app.api.v1.paging import Page, page_limit, sliced
from app.core.database import get_db
from app.core.security import require_auth
from app.core.uploads import file_response, store_upload, unlink
from app.models.file import File
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
    created_at: datetime
    files: list[FileOut] = []


def _owned(note_id: int, user: User, db: Session) -> Note:
    note = db.get(Note, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(404, "Note not found")
    return note


@router.get("/notes", response_model=Page[NoteOut])
def list_notes(
    before_id: int | None = None,
    limit: int = Depends(page_limit),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    q = select(Note).where(Note.user_id == user.id)
    if before_id is not None:
        q = q.where(Note.id < before_id)
    rows = db.scalars(q.options(selectinload(Note.files)).order_by(Note.id.desc()).limit(limit + 1)).all()
    items, has_more = sliced(rows, limit)
    return Page(items=items, has_more=has_more)


@router.post("/notes", response_model=NoteOut)
def create_note(data: NoteIn, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = Note(user_id=user.id, title=data.title, content=data.content, tags=data.tags, files=[])
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
    note = _owned(note_id, user, db)
    for item in list(note.files):
        unlink(item.stored)
        db.delete(item)
    db.delete(note)
    db.commit()


@router.post("/notes/{note_id}/files", response_model=FileOut)
def add_file(note_id: int, file: UploadFile, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    name, stored = store_upload(file)
    row = File(user_id=user.id, note_id=note.id, name=name, stored=stored)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/notes/{note_id}/files/{file_id}")
def get_file(note_id: int, file_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    row = db.get(File, file_id)
    if not row or row.note_id != note.id:
        raise HTTPException(404, "File not found")
    return file_response(row.stored, row.name)


@router.delete("/notes/{note_id}/files/{file_id}")
def delete_file(note_id: int, file_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    row = db.get(File, file_id)
    if not row or row.note_id != note.id:
        raise HTTPException(404, "File not found")
    unlink(row.stored)
    db.delete(row)
    db.commit()
