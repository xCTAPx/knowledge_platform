from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_auth
from app.core.uploads import file_response, store_upload, unlink
from app.models.note import NoteFile
from app.models.user import User

router = APIRouter()


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


def _owned_file(file_id: int, user: User, db: Session) -> NoteFile:
    row = db.get(NoteFile, file_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "File not found")
    return row


@router.get("/files", response_model=list[FileOut])
def list_files(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    return db.scalars(
        select(NoteFile).where(NoteFile.user_id == user.id, NoteFile.note_id.is_(None)).order_by(NoteFile.id.desc())
    ).all()


@router.post("/files", response_model=FileOut)
def add_file(file: UploadFile, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    name, stored = store_upload(file)
    row = NoteFile(user_id=user.id, note_id=None, name=name, stored=stored)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/files/{file_id}")
def get_file(file_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = _owned_file(file_id, user, db)
    return file_response(row.stored, row.name)


@router.delete("/files/{file_id}")
def delete_file(file_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = _owned_file(file_id, user, db)
    unlink(row.stored)
    db.delete(row)
    db.commit()
