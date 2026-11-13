import logging
import time
from collections.abc import Callable

from redis import Redis
from rq import Queue
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.vectors import drop_file, drop_note, has_chunks, index_file, index_note
from app.models.file import File
from app.models.note import Note
from app.models.outbox import Outbox

QUEUE = "index"
PENDING = "pending"
READY = "ready"
FAILED = "failed"
ATTEMPTS = 3
PAUSE = (5, 15)
JOB_TIMEOUT = 900
log = logging.getLogger(__name__)


def _enqueue(func: Callable[..., None], *args: int) -> None:
    Queue(QUEUE, connection=Redis.from_url(settings.redis_url)).enqueue(func, *args, job_timeout=JOB_TIMEOUT)


def _stage(db: Session, kind: str, item_id: int, gen: int) -> None:
    queued = db.scalar(select(Outbox.id).where(Outbox.kind == kind, Outbox.item_id == item_id, Outbox.gen == gen).limit(1))
    if queued is None:
        db.add(Outbox(kind=kind, item_id=item_id, gen=gen))


def queue_note(note: Note, db: Session) -> None:
    note.index_status = PENDING
    note.index_gen = (note.index_gen or 0) + 1
    db.add(note)
    db.flush()
    db.add(Outbox(kind="note", item_id=note.id, gen=note.index_gen))
    db.commit()
    db.refresh(note)


def queue_file(row: File, db: Session) -> None:
    row.index_status = PENDING
    db.add(row)
    db.flush()
    db.add(Outbox(kind="file", item_id=row.id, gen=0))
    db.commit()
    db.refresh(row)


def publish_outbox(db: Session) -> None:
    rows = db.scalars(select(Outbox).order_by(Outbox.id).limit(100)).all()
    for row in rows:
        if row.kind == "note":
            _enqueue(run_index_note, row.item_id, row.gen)
        else:
            _enqueue(run_index_file, row.item_id)
        db.delete(row)
        db.commit()


def relay() -> None:
    while True:
        db = SessionLocal()
        try:
            publish_outbox(db)
        except Exception:
            log.exception("outbox relay failed")
            db.rollback()
        finally:
            db.close()
        time.sleep(1)


def resume(db: Session) -> None:
    if not has_chunks():
        for note in db.scalars(select(Note)).all():
            note.index_status = PENDING
            _stage(db, "note", note.id, note.index_gen)
        for row in db.scalars(select(File)).all():
            row.index_status = PENDING
            _stage(db, "file", row.id, 0)
        db.commit()
        return
    for note in db.scalars(select(Note).where(Note.index_status == PENDING)).all():
        _stage(db, "note", note.id, note.index_gen)
    for row in db.scalars(select(File).where(File.index_status == PENDING)).all():
        _stage(db, "file", row.id, 0)
    db.commit()


def _tries(work, fail) -> None:
    for attempt in range(ATTEMPTS):
        try:
            work()
            return
        except Exception:
            log.exception("index attempt %s failed", attempt + 1)
            if attempt + 1 == ATTEMPTS:
                fail()
                return
            time.sleep(PAUSE[attempt])


def _finish_note(note_id: int, gen: int) -> None:
    db = SessionLocal()
    try:
        note = db.get(Note, note_id)
        if note is None or note.index_gen != gen:
            return
        user_id = note.user_id
        index_note(note)
        db.expire_all()
        note = db.get(Note, note_id)
        if note is None:
            drop_note(user_id, note_id, [])
            return
        if note.index_gen != gen:
            return
        note.index_status = READY
        db.commit()
    finally:
        db.close()


def _fail_note(note_id: int, gen: int) -> None:
    db = SessionLocal()
    try:
        note = db.get(Note, note_id)
        if note is None or note.index_gen != gen:
            return
        note.index_status = FAILED
        db.commit()
    finally:
        db.close()


def run_index_note(note_id: int, gen: int) -> None:
    _tries(lambda: _finish_note(note_id, gen), lambda: _fail_note(note_id, gen))


def _finish_file(file_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.get(File, file_id)
        if row is None:
            return
        user_id = row.user_id
        index_file(row)
        db.expire_all()
        current = db.get(File, file_id)
        if current is None:
            drop_file(user_id, file_id)
            return
        current.index_status = READY
        db.commit()
    finally:
        db.close()


def _fail_file(file_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.get(File, file_id)
        if row is None:
            return
        row.index_status = FAILED
        db.commit()
    finally:
        db.close()


def run_index_file(file_id: int) -> None:
    _tries(lambda: _finish_file(file_id), lambda: _fail_file(file_id))
