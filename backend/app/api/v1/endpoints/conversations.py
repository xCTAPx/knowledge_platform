from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.library import library_excerpts
from app.core.llm import complete, stream
from app.core.security import require_auth
from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User

router = APIRouter()
HISTORY = 20


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationIn(BaseModel):
    title: str


class MessageIn(BaseModel):
    text: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    text: str
    created_at: datetime


def _owned(conversation_id: int, user: User, db: Session) -> Conversation:
    row = db.get(Conversation, conversation_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return row


def _count(conversation_id: int, db: Session) -> int:
    return db.scalar(select(func.count()).select_from(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id)) or 0


def _out(row: Conversation, n: int) -> ConversationOut:
    return ConversationOut(id=row.id, title=row.title, created_at=row.created_at, updated_at=row.updated_at, message_count=n)


def _draft_title(text: str) -> str:
    return " ".join(text.split())[:60]


def _smart_title(question: str, answer: str) -> str:
    try:
        raw = complete(
            f"Question:\n{question[:400]}\n\nAnswer:\n{answer[:400]}",
            "Reply with a chat title only: 3 to 6 words, same language as the question, no quotes.",
        )
    except HTTPException:
        return ""
    line = raw.splitlines()[0].strip(" \"'`") if raw else ""
    return line[:80]


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    n_msgs = (
        select(func.count(ConversationMessage.id))
        .where(ConversationMessage.conversation_id == Conversation.id)
        .correlate(Conversation)
        .scalar_subquery()
    )
    rows = db.execute(
        select(Conversation, n_msgs).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    ).all()
    return [_out(row, n or 0) for row, n in rows]


@router.post("/conversations", response_model=ConversationOut)
def create_conversation(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = Conversation(user_id=user.id, title="New chat")
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(row, 0)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = _owned(conversation_id, user, db)
    return _out(row, _count(row.id, db))


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def rename_conversation(conversation_id: int, data: ConversationIn, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = _owned(conversation_id, user, db)
    title = data.title.strip()
    if not title:
        raise HTTPException(400, "Title is required")
    row.title = title[:255]
    db.commit()
    db.refresh(row)
    return _out(row, _count(row.id, db))


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = _owned(conversation_id, user, db)
    db.delete(row)
    db.commit()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    _owned(conversation_id, user, db)
    return db.scalars(select(ConversationMessage).where(ConversationMessage.conversation_id == conversation_id).order_by(ConversationMessage.id)).all()


@router.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: int, data: MessageIn, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    row = _owned(conversation_id, user, db)
    text = data.text.strip()
    if not text:
        raise HTTPException(400, "Ask a question")
    needs_title = not _count(row.id, db) or row.title == "New chat"
    if needs_title:
        row.title = _draft_title(text)
    db.add(ConversationMessage(conversation_id=row.id, role="user", text=text))
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    prior = db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == row.id)
        .order_by(ConversationMessage.id.desc())
        .limit(HISTORY)
    ).all()[::-1]
    chat = "\n".join(f"{msg.role}: {msg.text}" for msg in prior)
    prompt = f"Chat:\n{chat}\n\nLibrary:\n{library_excerpts(text, user, db)}"
    conv_id = row.id

    def chunks():
        acc: list[bytes] = []
        try:
            for piece in stream(prompt):
                acc.append(piece)
                yield piece
        finally:
            body = b"".join(acc).decode()
            if not body:
                return
            extra = SessionLocal()
            try:
                extra.add(ConversationMessage(conversation_id=conv_id, role="assistant", text=body))
                conv = extra.get(Conversation, conv_id)
                if conv:
                    conv.updated_at = datetime.now(timezone.utc)
                    if needs_title:
                        titled = _smart_title(text, body)
                        if titled:
                            conv.title = titled
                extra.commit()
            finally:
                extra.close()

    return StreamingResponse(
        chunks(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
