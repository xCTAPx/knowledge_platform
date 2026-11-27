import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import httpx
from qdrant_client.common.client_exceptions import ResourceExhaustedResponse
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from tenacity import RetryCallState, Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter
from urllib3.exceptions import InvalidHeader
from urllib3.util.retry import Retry

from redis import Redis
from rq import Queue
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.vectors import drop_file, drop_note, has_chunks, index_file, index_note
from app.models.file import File
from app.models.note import Note
from app.models.outbox import Outbox

INDEX = "index"
DROP = "drop"
PENDING = "pending"
READY = "ready"
FAILED = "failed"
ATTEMPTS = 3
BACKOFF = 5
MAX_PAUSE = 120
JOB_TIMEOUT = 900
log = logging.getLogger(__name__)


def _enqueue(queue: str, func: Callable[..., None], *args: int) -> None:
    Queue(queue, connection=Redis.from_url(settings.redis_url)).enqueue(func, *args, job_timeout=JOB_TIMEOUT)


def _stage(db: Session, kind: str, item_id: int, gen: int) -> None:
    queued = db.scalar(select(Outbox.id).where(Outbox.kind == kind, Outbox.item_id == item_id, Outbox.gen == gen).limit(1))
    if queued is None:
        db.add(Outbox(kind=kind, item_id=item_id, gen=gen))


def queue_index_note(note: Note, db: Session) -> None:
    note.index_status = PENDING
    note.index_gen = (note.index_gen or 0) + 1
    db.add(note)
    db.flush()
    db.add(Outbox(kind="note", item_id=note.id, gen=note.index_gen))
    db.commit()
    db.refresh(note)


def queue_index_file(row: File, db: Session) -> None:
    row.index_status = PENDING
    db.add(row)
    db.flush()
    db.add(Outbox(kind="file", item_id=row.id, gen=0))
    db.commit()
    db.refresh(row)


def queue_drop_note(user_id: int, note_id: int, file_ids: list[int], db: Session) -> None:
    for file_id in file_ids:
        db.add(Outbox(kind="drop_file", item_id=file_id, gen=0, user_id=user_id))
    db.add(Outbox(kind="drop_note", item_id=note_id, gen=0, user_id=user_id))


def queue_drop_file(user_id: int, file_id: int, db: Session) -> None:
    db.add(Outbox(kind="drop_file", item_id=file_id, gen=0, user_id=user_id))


def _publish(row: Outbox) -> bool:
    if row.kind == "note":
        _enqueue(INDEX, run_index_note, row.item_id, row.gen)
    elif row.kind == "file":
        _enqueue(INDEX, run_index_file, row.item_id)
    elif row.user_id is None:
        log.error("drop outbox %s missing user_id", row.id)
        return False
    elif row.kind == "drop_note":
        _enqueue(DROP, run_drop_note, row.user_id, row.item_id)
    elif row.kind == "drop_file":
        _enqueue(DROP, run_drop_file, row.user_id, row.item_id)
    else:
        log.error("unknown outbox kind %s", row.kind)
        return False
    return True


def publish_outbox(db: Session) -> None:
    stale = datetime.now(timezone.utc) - timedelta(seconds=JOB_TIMEOUT)
    due = or_(Outbox.published_at.is_(None), Outbox.published_at < stale)
    rows = db.scalars(select(Outbox).where(due).order_by(Outbox.id).limit(100)).all()
    for row in rows:
        if _publish(row):
            row.published_at = datetime.now(timezone.utc)
        else:
            db.delete(row)
        db.commit()


def _done(db: Session, kind: str, item_id: int, gen: int) -> None:
    for row in db.scalars(select(Outbox).where(Outbox.kind == kind, Outbox.item_id == item_id, Outbox.gen == gen)).all():
        db.delete(row)


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


_retry_after_header = Retry(retry_after_max=MAX_PAUSE)


def _retry_after(exc: BaseException) -> float | None:
    if isinstance(exc, ResourceExhaustedResponse):
        return float(exc.retry_after_s)
    if isinstance(exc, UnexpectedResponse):
        raw = exc.headers.get("Retry-After")
        if raw:
            try:
                return _retry_after_header.parse_retry_after(raw)
            except InvalidHeader:
                return None
    return None


TEMPORARY_SERVER = {
    httpx.codes.BAD_GATEWAY,
    httpx.codes.SERVICE_UNAVAILABLE,
    httpx.codes.GATEWAY_TIMEOUT,
}


def _transient(exc: BaseException) -> bool:
    if isinstance(exc, ResourceExhaustedResponse):
        return True
    if isinstance(exc, UnexpectedResponse):
        return exc.status_code in TEMPORARY_SERVER or exc.status_code == httpx.codes.TOO_MANY_REQUESTS
    inner = exc.source if isinstance(exc, ResponseHandlingException) else exc
    return isinstance(inner, (httpx.TransportError, TimeoutError, ConnectionError))


_backoff = wait_exponential_jitter(multiplier=BACKOFF, max=MAX_PAUSE, jitter=BACKOFF)


def _wait(retry_state: RetryCallState) -> float:
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    hinted = _retry_after(exc) if exc is not None else None
    if hinted is not None:
        return min(hinted, MAX_PAUSE)
    return _backoff(retry_state)


def _before_sleep(retry_state: RetryCallState) -> None:
    log.error(
        "index attempt %s failed, retry in %.1fs",
        retry_state.attempt_number,
        retry_state.upcoming_sleep,
        exc_info=retry_state.outcome.exception() if retry_state.outcome else None,
    )


def _tries(work, fail) -> None:
    retrying = Retrying(
        stop=stop_after_attempt(ATTEMPTS),
        wait=_wait,
        retry=retry_if_exception(_transient),
        before_sleep=_before_sleep,
        reraise=True,
    )
    try:
        retrying(work)
    except Exception:
        log.exception("index attempt %s failed", retrying.statistics["attempt_number"])
        fail()


def _finish_note(note_id: int, gen: int) -> None:
    db = SessionLocal()
    try:
        note = db.get(Note, note_id)
        if note is None or note.index_gen != gen:
            _done(db, "note", note_id, gen)
            db.commit()
            return
        user_id = note.user_id
        index_note(note)
        db.expire_all()
        note = db.get(Note, note_id)
        if note is None:
            drop_note(user_id, note_id, [])
            _done(db, "note", note_id, gen)
            db.commit()
            return
        if note.index_gen != gen:
            _done(db, "note", note_id, gen)
            db.commit()
            return
        note.index_status = READY
        _done(db, "note", note_id, gen)
        db.commit()
    finally:
        db.close()


def _fail_note(note_id: int, gen: int) -> None:
    db = SessionLocal()
    try:
        note = db.get(Note, note_id)
        if note is not None and note.index_gen == gen:
            note.index_status = FAILED
        _done(db, "note", note_id, gen)
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
            _done(db, "file", file_id, 0)
            db.commit()
            return
        user_id = row.user_id
        index_file(row)
        db.expire_all()
        current = db.get(File, file_id)
        if current is None:
            drop_file(user_id, file_id)
            _done(db, "file", file_id, 0)
            db.commit()
            return
        current.index_status = READY
        _done(db, "file", file_id, 0)
        db.commit()
    finally:
        db.close()


def _fail_file(file_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.get(File, file_id)
        if row is not None:
            row.index_status = FAILED
        _done(db, "file", file_id, 0)
        db.commit()
    finally:
        db.close()


def run_index_file(file_id: int) -> None:
    _tries(lambda: _finish_file(file_id), lambda: _fail_file(file_id))


def _drop(kind: str, item_id: int, drop) -> None:
    drop()
    db = SessionLocal()
    try:
        _done(db, kind, item_id, 0)
        db.commit()
    finally:
        db.close()


def run_drop_note(user_id: int, note_id: int) -> None:
    _tries(lambda: _drop("drop_note", note_id, lambda: drop_note(user_id, note_id, [])), lambda: None)


def run_drop_file(user_id: int, file_id: int) -> None:
    _tries(lambda: _drop("drop_file", file_id, lambda: drop_file(user_id, file_id)), lambda: None)
