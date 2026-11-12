import logging
import threading
from dataclasses import dataclass
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PayloadSchemaType, PointStruct, VectorParams

from app.core.chunks import file_text, split_text
from app.core.config import settings
from app.core.embeddings import embed
from app.core.uploads import UPLOAD_DIR
from app.models.file import File
from app.models.note import Note

COLLECTION = "chunks"
DIM = 1024
log = logging.getLogger(__name__)
_client: QdrantClient | None = None
_hidden: set[tuple[int, str, int]] = set()
_hidden_lock = threading.Lock()


def conceal(user_id: int, source: str, item_id: int) -> None:
    with _hidden_lock:
        _hidden.add((user_id, source, item_id))


def reveal(user_id: int, source: str, item_id: int) -> None:
    with _hidden_lock:
        _hidden.discard((user_id, source, item_id))


def _concealed(user_id: int, source: str, item_id: int | None) -> bool:
    if item_id is None:
        return False
    with _hidden_lock:
        return (user_id, source, item_id) in _hidden


def _excluded(user_id: int) -> list[Filter]:
    with _hidden_lock:
        pending = [item for item in _hidden if item[0] == user_id]
    excluded: list[Filter] = []
    for _owner, source, item_id in pending:
        field = "file_id" if source == "file" else "note_id"
        excluded.append(
            Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=source)),
                    FieldCondition(key=field, match=MatchValue(value=item_id)),
                ]
            )
        )
    return excluded


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
    try:
        ensure_collection()
        _delete(user_id, "note", "note_id", note_id)
    except Exception:
        log.exception("failed to drop note %s from qdrant", note_id)
    else:
        reveal(user_id, "note", note_id)
    for file_id in file_ids:
        drop_file(user_id, file_id)


def drop_file(user_id: int, file_id: int) -> None:
    try:
        ensure_collection()
        _delete(user_id, "file", "file_id", file_id)
    except Exception:
        log.exception("failed to drop file %s from qdrant", file_id)
        return
    reveal(user_id, "file", file_id)


@dataclass(frozen=True)
class ChunkHit:
    rank: int
    score: float
    text: str
    source: str
    title: str
    note_id: int | None
    file_id: int | None


def _user_filter(user_id: int) -> Filter:
    excluded = _excluded(user_id)
    return Filter(
        must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))],
        must_not=excluded or None,
    )


def _visible_hit(user_id: int, payload: dict | None, score: float) -> ChunkHit | None:
    payload = payload or {}
    body = payload.get("text")
    if not body:
        return None
    note_id = payload.get("note_id")
    file_id = payload.get("file_id")
    source = str(payload.get("source") or "")
    note_key = int(note_id) if note_id is not None else None
    file_key = int(file_id) if file_id is not None else None
    if _concealed(user_id, "file", file_key) or (source == "note" and _concealed(user_id, "note", note_key)):
        return None
    return ChunkHit(
        rank=0,
        score=score,
        text=str(body),
        source=source,
        title=str(payload.get("title") or ""),
        note_id=note_key,
        file_id=file_key,
    )


def user_chunks(user_id: int) -> list[ChunkHit]:
    hits: list[ChunkHit] = []
    offset = None
    while True:
        records, offset = _qdrant().scroll(
            collection_name=COLLECTION,
            scroll_filter=_user_filter(user_id),
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for record in records:
            hit = _visible_hit(user_id, record.payload, 0.0)
            if hit is not None:
                hits.append(hit)
        if offset is None:
            break
    return hits


def nearest_chunks(query: str, user_id: int, limit: int) -> list[ChunkHit]:
    text = query.strip()
    if not text:
        return []
    ensure_collection()
    found = _qdrant().query_points(
        collection_name=COLLECTION,
        query=embed([text])[0],
        query_filter=_user_filter(user_id),
        limit=limit,
        with_payload=True,
    ).points
    hits: list[ChunkHit] = []
    for point in found:
        hit = _visible_hit(user_id, point.payload, float(point.score))
        if hit is not None:
            hits.append(hit)
    return hits


def has_chunks() -> bool:
    ensure_collection()
    return _qdrant().count(COLLECTION, exact=True).count > 0
