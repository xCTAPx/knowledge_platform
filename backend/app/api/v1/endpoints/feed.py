from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import exists, literal, or_, select, tuple_, union_all
from sqlalchemy.orm import Session, selectinload

from app.api.v1.endpoints.files import FileOut
from app.api.v1.endpoints.notes import NoteOut
from app.api.v1.paging import Page, contains, page_limit, sliced
from app.core.database import get_db
from app.core.security import require_auth
from app.models.file import File
from app.models.note import Note
from app.models.user import User

router = APIRouter()


class FeedNote(NoteOut):
    kind: Literal["note"] = "note"


class FeedFile(FileOut):
    kind: Literal["file"] = "file"


FeedItem = Annotated[FeedNote | FeedFile, Field(discriminator="kind")]


@router.get("/feed", response_model=Page[FeedItem])
def list_feed(
    q: str | None = None,
    before_id: int | None = None,
    before_kind: Literal["note", "file"] | None = None,
    before_created_at: datetime | None = None,
    limit: int = Depends(page_limit),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    notes_q = select(literal("note").label("kind"), Note.id, Note.created_at).where(Note.user_id == user.id)
    files_q = select(literal("file").label("kind"), File.id, File.created_at).where(
        File.user_id == user.id, File.note_id.is_(None)
    )
    term = (q or "").strip()
    if term:
        attached = exists().where(File.note_id == Note.id, contains(File.name, term))
        notes_q = notes_q.where(or_(contains(Note.title, term), contains(Note.content, term), attached))
        files_q = files_q.where(contains(File.name, term))
    feed = union_all(notes_q, files_q).subquery("feed")
    stmt = select(feed.c.kind, feed.c.id, feed.c.created_at).order_by(
        feed.c.created_at.desc(), feed.c.kind.desc(), feed.c.id.desc()
    )
    if before_id is not None and before_kind is not None and before_created_at is not None:
        stmt = stmt.where(tuple_(feed.c.created_at, feed.c.kind, feed.c.id) < (before_created_at, before_kind, before_id))
    rows = db.execute(stmt.limit(limit + 1)).all()
    rows, has_more = sliced(rows, limit)
    note_ids = [row.id for row in rows if row.kind == "note"]
    file_ids = [row.id for row in rows if row.kind == "file"]
    notes = (
        {note.id: note for note in db.scalars(select(Note).where(Note.id.in_(note_ids)).options(selectinload(Note.files)))}
        if note_ids
        else {}
    )
    files = {item.id: item for item in db.scalars(select(File).where(File.id.in_(file_ids)))} if file_ids else {}
    items: list[FeedNote | FeedFile] = []
    for row in rows:
        if row.kind == "note":
            note = notes.get(row.id)
            if note is not None:
                items.append(FeedNote.model_validate(note))
        else:
            item = files.get(row.id)
            if item is not None:
                items.append(FeedFile.model_validate(item))
    return Page(items=items, has_more=has_more)
