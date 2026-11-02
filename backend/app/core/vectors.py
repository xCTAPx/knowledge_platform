from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PayloadSchemaType, PointStruct, VectorParams
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.chunks import file_text, split_text
from app.core.config import settings
from app.core.embeddings import embed
from app.core.uploads import UPLOAD_DIR
from app.models.file import File
from app.models.note import Note

COLLECTION = "chunks"
DIM = 1024
TOP_K = 5

_client: QdrantClient | None = None


def _qdrant() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url)
    return _client


def ensure_collection() -> None:
    client = _qdrant()
    if client.collection_exists(COLLECTION):
        return
    client.create_collection(collection_name=COLLECTION, vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))
    for field in ("user_id", "note_id", "file_id"):
        client.create_payload_index(COLLECTION, field, field_schema=PayloadSchemaType.INTEGER)
    client.create_payload_index(COLLECTION, "source", field_schema=PayloadSchemaType.KEYWORD)


def _delete(user_id: int, source: str, field: str, value: int) -> None:
    _qdrant().delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                FieldCondition(key="source", match=MatchValue(value=source)),
                FieldCondition(key=field, match=MatchValue(value=value)),
            ]
        ),
    )


def _upsert(user_id: int, source: str, chunks: list[str], payload: dict) -> None:
    if not chunks:
        return
    vectors = embed(chunks)
    client = _qdrant()
    batch = 32
    for start in range(0, len(chunks), batch):
        points = [
            PointStruct(id=str(uuid4()), vector=vector, payload={"text": text, "user_id": user_id, "source": source, **payload})
            for text, vector in zip(chunks[start : start + batch], vectors[start : start + batch])
        ]
        client.upsert(collection_name=COLLECTION, points=points)


def index_note(note: Note) -> None:
    ensure_collection()
    _delete(note.user_id, "note", "note_id", note.id)
    _upsert(
        note.user_id,
        "note",
        split_text(note.content, note.title, True),
        {"note_id": note.id, "title": note.title, "tags": list(note.tags or [])},
    )


def index_file(item: File) -> None:
    ensure_collection()
    _delete(item.user_id, "file", "file_id", item.id)
    payload: dict = {"file_id": item.id, "title": item.name}
    if item.note_id is not None:
        payload["note_id"] = item.note_id
    markdown = item.stored.lower().endswith(".md")
    _upsert(item.user_id, "file", split_text(file_text(UPLOAD_DIR / item.stored), item.name, markdown), payload)


def drop_note(user_id: int, note_id: int, file_ids: list[int]) -> None:
    ensure_collection()
    _delete(user_id, "note", "note_id", note_id)
    for file_id in file_ids:
        _delete(user_id, "file", "file_id", file_id)


def drop_file(user_id: int, file_id: int) -> None:
    ensure_collection()
    _delete(user_id, "file", "file_id", file_id)


def search_chunks(query: str, user_id: int) -> list[str]:
    text = query.strip()
    if not text:
        return []
    ensure_collection()
    found = _qdrant().query_points(
        collection_name=COLLECTION,
        query=embed([text])[0],
        query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
        limit=TOP_K,
        with_payload=True,
    ).points
    return [str(point.payload["text"]) for point in found if point.payload and point.payload.get("text")]


def backfill_library(db: Session) -> None:
    ensure_collection()
    if _qdrant().count(COLLECTION, exact=True).count:
        return
    for note in db.scalars(select(Note)).all():
        index_note(note)
    for item in db.scalars(select(File)).all():
        index_file(item)
