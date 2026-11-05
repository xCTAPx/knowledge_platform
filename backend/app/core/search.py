from dataclasses import replace

from app.core.bm25 import top_matches
from app.core.rerank import rerank
from app.core.vectors import ChunkHit, nearest_chunks, user_chunks

TOP_K = 5
RETRIEVE_K = 20


def search_chunks(query: str, user_id: int) -> list[ChunkHit]:
    text = query.strip()
    if not text:
        return []
    hits = nearest_chunks(text, user_id, RETRIEVE_K)
    seen = {hit.text for hit in hits}
    library = user_chunks(user_id)
    for index in top_matches(text, [hit.text for hit in library], RETRIEVE_K):
        candidate = library[index]
        if candidate.text in seen:
            continue
        hits.append(candidate)
        seen.add(candidate.text)
    if not hits:
        return []
    scores = rerank(text, [hit.text for hit in hits])
    order = sorted(range(len(hits)), key=lambda i: scores[i], reverse=True)[:TOP_K]
    return [replace(hits[i], rank=place, score=scores[i]) for place, i in enumerate(order, start=1)]
