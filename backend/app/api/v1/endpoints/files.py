from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.paging import Page, page_limit, sliced
from app.core.database import get_db
from app.core.security import require_auth
from app.core.uploads import file_response, store_upload, unlink
from app.models.file import File
from app.models.user import User

router = APIRouter()


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime


def _owned_file(file_id: int, user: User, db: Session) -> File:
    row = db.get(File, file_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "File not found")
    return row


@router.get("/files", response_model=Page[FileOut])
def list_files(
    before_id: int | None = None,
    limit: int = Depends(page_limit),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    q = select(File).where(File.user_id == user.id, File.note_id.is_(None))
    if before_id is not None:
        q = q.where(File.id < before_id)
    rows = db.scalars(q.order_by(File.id.desc()).limit(limit + 1)).all()
    items, has_more = sliced(rows, limit)
    return Page(items=items, has_more=has_more)


@router.post("/files", response_model=FileOut)
def add_file(file: UploadFile, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    name, stored = store_upload(file)
    row = File(user_id=user.id, note_id=None, name=name, stored=stored)
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
