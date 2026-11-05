from FlagEmbedding import FlagReranker

from app.core.config import settings
from app.core.inference import DEVICE, RERANK_BATCH_SIZE, RERANK_MAX_LENGTH, USE_FP16

_reranker: FlagReranker | None = None


def load_reranker() -> FlagReranker:
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(
            settings.rerank_model,
            use_fp16=USE_FP16,
            devices=DEVICE,
            max_length=RERANK_MAX_LENGTH,
            batch_size=RERANK_BATCH_SIZE,
            normalize=True,
        )
    return _reranker


def rerank(query: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    scores = load_reranker().compute_score([(query, passage) for passage in passages])
    return [float(score) for score in scores]
