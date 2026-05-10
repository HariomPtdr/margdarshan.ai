"""Lazy-loaded S-BERT embedder for semantic dedup.

Model: paraphrase-multilingual-MiniLM-L12-v2
  - 117 MB, 384-dim vectors
  - Handles Hindi, Hinglish, English in the same vector space
  - Downloaded once to ~/.cache/huggingface on first use

Falls back gracefully: if model is not yet loaded, dedup skips similarity
and returns is_duplicate=False so the pipeline never stalls.
"""

import logging
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model = None
_model_lock = threading.Lock()
_load_attempted = False

SIMILARITY_THRESHOLD = 0.85


def _try_load() -> None:
    global _model, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
        logger.info("S-BERT model loaded: %s", _MODEL_NAME)
    except Exception as e:
        logger.warning("S-BERT model could not be loaded (%s) — dedup will use exact match", e)


def is_ready() -> bool:
    return _model is not None


def embed(text: str) -> Optional[list[float]]:
    """Return 384-dim embedding as a plain Python float list, or None if model not ready."""
    with _model_lock:
        _try_load()
        if _model is None:
            return None
    vec = _model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def is_duplicate(new_embedding: list[float], candidate_embeddings: list[list[float]]) -> bool:
    """Return True if any candidate is semantically similar (cosine ≥ threshold)."""
    for emb in candidate_embeddings:
        if cosine_similarity(new_embedding, emb) >= SIMILARITY_THRESHOLD:
            return True
    return False
