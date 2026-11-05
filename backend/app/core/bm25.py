import re

from rank_bm25 import BM25Okapi

_TOKEN = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN.findall(text)]


def top_matches(query: str, documents: list[str], limit: int) -> list[int]:
    docs = [_tokens(document) for document in documents]
    terms = _tokens(query)
    if not terms or not docs:
        return []
    scores = BM25Okapi(docs).get_scores(terms)
    order = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
    return [i for i in order if scores[i] > 0][:limit]
