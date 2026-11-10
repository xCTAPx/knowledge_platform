from dataclasses import replace

from app.core.bm25 import top_matches
from app.core.rerank import rerank
from app.core.vectors import ChunkHit, nearest_chunks, user_chunks

TOP_K = 5
RETRIEVE_K = 20
MODE = "dense_rerank" # dense, bm25, dense_rerank, hybrid (dense + bm25 + rerank)


def _top_reranked(query: str, hits: list[ChunkHit]) -> list[ChunkHit]:
    if not hits:
        return []
    scores = rerank(query, [hit.text for hit in hits])
    order = sorted(range(len(hits)), key=lambda i: scores[i], reverse=True)[:TOP_K]
    return [replace(hits[i], rank=place, score=scores[i]) for place, i in enumerate(order, start=1)]


def search_chunks(query: str, user_id: int, mode: str | None = None) -> list[ChunkHit]:
    text = query.strip()
    if not text:
        return []
    mode = MODE if mode is None else mode
    if mode == "dense":
        hits = nearest_chunks(text, user_id, TOP_K)
        return [replace(hit, rank=place) for place, hit in enumerate(hits, start=1)]
    if mode == "dense_rerank":
        return _top_reranked(text, nearest_chunks(text, user_id, RETRIEVE_K))
    if mode == "bm25":
        library = user_chunks(user_id)
        indexes = top_matches(text, [hit.text for hit in library], TOP_K)
        return [replace(library[index], rank=place) for place, index in enumerate(indexes, start=1)]
    if mode != "hybrid":
        raise ValueError(f"unknown search mode: {mode}")
    hits = nearest_chunks(text, user_id, RETRIEVE_K)
    seen = {hit.text for hit in hits}
    library = user_chunks(user_id)
    for index in top_matches(text, [hit.text for hit in library], RETRIEVE_K):
        candidate = library[index]
        if candidate.text in seen:
            continue
        hits.append(candidate)
        seen.add(candidate.text)
    return _top_reranked(text, hits)
