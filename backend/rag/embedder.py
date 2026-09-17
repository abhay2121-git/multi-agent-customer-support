"""Embedding generation using HuggingFace Inference API (lightweight, no local model)."""

from __future__ import annotations

import logging
import os
import time

import numpy as np
import requests

from backend.config import settings

logger = logging.getLogger(__name__)

# HuggingFace free Inference API endpoint for the embedding model
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")  # Optional, increases rate limits


class EmbeddingModel:
    """Embedding model wrapper that calls HuggingFace Inference API instead of loading locally.

    This avoids loading PyTorch + sentence-transformers into RAM, keeping memory
    usage well under Render's free-tier 512MB limit.
    """

    def __init__(self) -> None:
        """Initialize the HuggingFace Inference API client."""
        self.model_name = settings.EMBEDDING_MODEL
        self.api_url = HF_API_URL.format(model=self.model_name)
        self.headers = {}
        if HF_API_TOKEN:
            self.headers["Authorization"] = f"Bearer {HF_API_TOKEN}"
        self._local_model = None  # Lazy-loaded fallback for local/build usage
        logger.info(
            "EmbeddingModel initialized with HF Inference API for: %s", self.model_name
        )

    def _call_hf_api(self, texts: list[str]) -> np.ndarray | None:
        """Call the HuggingFace Inference API for embeddings."""
        try:
            payload = {
                "inputs": texts,
                "options": {"wait_for_model": True},
            }
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            if response.status_code == 200:
                embeddings = np.array(response.json(), dtype=np.float32)
                # Normalize embeddings (same as sentence-transformers normalize_embeddings=True)
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1  # Avoid division by zero
                embeddings = embeddings / norms
                return embeddings
            else:
                logger.warning(
                    "HF API returned status %d: %s", response.status_code, response.text[:200]
                )
                return None
        except Exception as e:
            logger.warning("HF API call failed: %s", e)
            return None

    def _get_local_model(self):
        """Lazy-load the local sentence-transformers model as a fallback."""
        if self._local_model is None:
            try:
                logger.info("Attempting to load local sentence-transformers model...")
                from sentence_transformers import SentenceTransformer
                self._local_model = SentenceTransformer(self.model_name)
                logger.info("Local model loaded.")
            except Exception as e:
                logger.warning("Local sentence-transformers model unavailable: %s", e)
                return None
        return self._local_model

    def _embed_local(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings using the local model (fallback)."""
        try:
            model = self._get_local_model()
            if model is None:
                return np.empty((0, 0), dtype=np.float32)
            embeddings = model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return np.asarray(embeddings, dtype=np.float32)
        except Exception as e:
            logger.warning("Local embedding generation failed: %s", e)
            return np.empty((0, 0), dtype=np.float32)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Generate normalized embeddings for a list of texts.

        Tries HuggingFace Inference API first, falls back to local model if needed.
        """
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        start = time.time()

        # Try HF Inference API first (lightweight, no local model needed)
        try:
            result = self._call_hf_api(texts)
            if result is not None and result.size > 0:
                elapsed = time.time() - start
                logger.info(
                    "Generated embeddings for %d texts via HF API in %.2f seconds",
                    len(texts), elapsed,
                )
                return result
        except Exception as e:
            logger.warning("HF API error during embed_texts: %s", e)

        # Fallback to local model if available
        try:
            result = self._embed_local(texts)
            if result is not None and result.size > 0:
                elapsed = time.time() - start
                logger.info(
                    "Generated embeddings for %d texts via local model in %.2f seconds",
                    len(texts), elapsed,
                )
                return result
        except Exception as e:
            logger.warning("Local embedding error: %s", e)

        return np.empty((0, 0), dtype=np.float32)


    def embed_query(self, query: str) -> np.ndarray:
        """Generate a normalized embedding for a single query string."""
        return self.embed_texts([query])


embedding_model = EmbeddingModel()
