from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import require_auth
from app.models.note import Note, NoteFile
from app.models.user import User

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads"
ALLOWED = {".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8", ".md": "text/plain; charset=utf-8"}
MAX_BYTES = 10 * 1024 * 1024


class NoteIn(BaseModel):
    title: str
    content: str = ""
    tags: list[str] = []


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    tags: list[str]
    files: list[FileOut] = []


def _owned(note_id: int, user: User, db: Session) -> Note:
    note = db.get(Note, note_id)
    if not note or note.user_id != user.id:
        raise HTTPException(404, "Note not found")
    return note


def _unlink(stored: str) -> None:
    (UPLOAD_DIR / stored).unlink(missing_ok=True)


@router.get("/notes", response_model=list[NoteOut])
def list_notes(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    return db.scalars(
        select(Note).where(Note.user_id == user.id).options(selectinload(Note.files)).order_by(Note.id.desc())
    ).all()


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
    for item in note.files:
        _unlink(item.stored)
    db.delete(note)
    db.commit()


@router.post("/notes/{note_id}/files", response_model=FileOut)
def add_file(note_id: int, file: UploadFile, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Only PDF, txt, and Markdown files are allowed")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File is too large")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{suffix}"
    (UPLOAD_DIR / stored).write_bytes(data)
    name = Path(file.filename).name[:255] if file.filename else f"file{suffix}"
    row = NoteFile(note_id=note.id, name=name, stored=stored)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/notes/{note_id}/files/{file_id}")
def get_file(note_id: int, file_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    row = db.get(NoteFile, file_id)
    if not row or row.note_id != note.id:
        raise HTTPException(404, "File not found")
    path = UPLOAD_DIR / row.stored
    if not path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type=ALLOWED[path.suffix.lower()], filename=row.name, content_disposition_type="inline")


@router.delete("/notes/{note_id}/files/{file_id}")
def delete_file(note_id: int, file_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    note = _owned(note_id, user, db)
    row = db.get(NoteFile, file_id)
    if not row or row.note_id != note.id:
        raise HTTPException(404, "File not found")
    _unlink(row.stored)
    db.delete(row)
    db.commit()
