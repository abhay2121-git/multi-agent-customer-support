"""Embedding generation utilities using sentence-transformers."""

from __future__ import annotations

import logging
import time

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Singleton-friendly embedding model wrapper for batched text vectorization."""

    def __init__(self) -> None:
        """Load sentence-transformers model configured in settings and log load time."""
        start = time.time()
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        elapsed = time.time() - start
        logger.info("Embedding model loaded in %.2f seconds", elapsed)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Generate normalized embeddings for a list of texts."""
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        start = time.time()
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        elapsed = time.time() - start
        logger.info("Generated embeddings for %d texts in %.2f seconds", len(texts), elapsed)

        return np.asarray(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Generate a normalized embedding for a single query string."""
        return self.embed_texts([query])


embedding_model = EmbeddingModel()
