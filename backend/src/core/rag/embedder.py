"""
Wrapper sentence-transformers — modelo multilíngue local.
Singleton para não recarregar o modelo a cada chamada.
"""
from typing import List, Optional
import structlog

log = structlog.get_logger()

_model = None
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DIM = 384


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        log.info("embedder.loading", model=MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
        log.info("embedder.ready")
    return _model


def embed(texts: List[str]) -> List[List[float]]:
    """Retorna lista de vetores (float32 → float para o Qdrant)."""
    model = get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_one(text: str) -> List[float]:
    return embed([text])[0]
