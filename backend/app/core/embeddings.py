from FlagEmbedding import BGEM3FlagModel
from app.core.config import settings

_model: BGEM3FlagModel | None = None


def load_embedder() -> BGEM3FlagModel:
    global _model
    if _model is None:
        _model = BGEM3FlagModel(
            settings.embed_model,
            use_fp16=True,
            devices="cuda:0",
            passage_max_length=2048,
        )
        _model.model.to("cuda:0")
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return load_embedder().encode(texts)["dense_vecs"].tolist()
