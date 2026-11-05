from FlagEmbedding import BGEM3FlagModel

from app.core.config import settings
from app.core.inference import DEVICE, EMBED_BATCH_SIZE, EMBED_MAX_LENGTH, USE_FP16

_model: BGEM3FlagModel | None = None


def load_embedder() -> BGEM3FlagModel:
    global _model
    if _model is None:
        _model = BGEM3FlagModel(
            settings.embed_model,
            use_fp16=USE_FP16,
            devices=DEVICE,
            batch_size=EMBED_BATCH_SIZE,
            passage_max_length=EMBED_MAX_LENGTH,
        )
        _model.model.to("cuda:0")
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return load_embedder().encode(texts)["dense_vecs"].tolist()
