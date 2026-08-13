import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

_model = None


def semantic_scores(jd: str, resumes: list[str]) -> list[float]:
    """Batch semantic similarity. Gracefully uses token overlap if model is unavailable."""
    global _model
    try:
        if _model is None:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        vectors = _model.encode([jd, *resumes], normalize_embeddings=True)
        return [round(float((cosine_similarity([vectors[0]], [v])[0][0] + 1) * 50), 2) for v in vectors[1:]]
    except Exception:
        jd_words = set(jd.lower().split())
        return [round(100 * len(jd_words & set(r.lower().split())) / max(len(jd_words), 1), 2) for r in resumes]
