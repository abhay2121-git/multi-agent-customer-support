"""FAISS vector store utilities for indexing and retrieving document chunks."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from backend.config import settings
from backend.rag.embedder import embedding_model

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store that builds, persists, loads, and searches chunk embeddings."""

    def __init__(self) -> None:
        """Initialize vector store paths and in-memory state."""
        self.index: faiss.Index | None = None
        self.chunks: list[dict[str, Any]] = []

        base_path = Path(settings.FAISS_INDEX_PATH)
        self.index_path = base_path.with_suffix(".index")
        self.metadata_path = base_path.with_name(base_path.name + "_metadata.json")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def build_index(self, chunks: list[dict[str, Any]]) -> None:
        """Build a FAISS inner-product index from chunk embeddings and persist it to disk."""
        if not chunks:
            raise ValueError("Cannot build index with empty chunk list.")

        start = time.time()

        texts = [str(chunk.get("text", "")) for chunk in chunks]
        embeddings = embedding_model.embed_texts(texts)
        if embeddings.size == 0:
            raise ValueError("No embeddings generated for chunk list.")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.chunks = chunks

        faiss.write_index(self.index, str(self.index_path))
        with self.metadata_path.open("w", encoding="utf-8") as metadata_file:
            json.dump(self.chunks, metadata_file, ensure_ascii=False, indent=2)

        elapsed = time.time() - start
        logger.info(
            "Built FAISS index with %d vectors in %.2f seconds",
            self.index.ntotal if self.index else 0,
            elapsed,
        )

    def load_index(self) -> bool:
        """Load persisted FAISS index and chunk metadata from disk if available."""
        if not self.index_path.exists() or not self.metadata_path.exists():
            logger.warning("FAISS index or metadata file not found at %s", self.index_path)
            return False

        try:
            self.index = faiss.read_index(str(self.index_path))
            with self.metadata_path.open("r", encoding="utf-8") as metadata_file:
                self.chunks = json.load(metadata_file)

            logger.info("Loaded FAISS index with %d vectors", self.index.ntotal)
            return True
        except Exception as e:
            logger.error("Failed to load FAISS index: %s", e)
            return False

    def auto_build_if_missing(self) -> bool:
        """Automatically build the FAISS index from knowledge_base if it doesn't exist.

        Returns True if the index is now available, False otherwise.
        """
        if self.index is not None and self.chunks:
            return True

        # Try loading from disk first
        if self.load_index():
            return True

        # Index not on disk — try building from knowledge_base
        logger.info("No FAISS index found. Attempting auto-build from knowledge_base/...")
        try:
            from backend.rag.loader import load_all_documents
            from backend.rag.chunker import chunk_all_documents

            # Resolve knowledge_base path relative to project root
            kb_path = Path("knowledge_base")
            if not kb_path.exists():
                # Try relative to the project directory
                project_root = Path(__file__).parent.parent.parent
                kb_path = project_root / "knowledge_base"

            if not kb_path.exists():
                logger.error(
                    "Cannot auto-build index: knowledge_base/ directory not found. "
                    "Run 'python -m backend.rag.build_index' manually."
                )
                return False

            documents = load_all_documents(str(kb_path))
            if not documents:
                logger.error(
                    "Cannot auto-build index: no documents found in %s. "
                    "Add .txt or .pdf files to knowledge_base/.",
                    kb_path,
                )
                return False

            chunks = chunk_all_documents(documents)
            if not chunks:
                logger.error("Cannot auto-build index: chunking produced no chunks.")
                return False

            self.build_index(chunks)
            logger.info("Auto-built FAISS index successfully with %d chunks.", len(chunks))
            return True

        except Exception as e:
            logger.error("Auto-build of FAISS index failed: %s", e, exc_info=True)
            return False

    def _fallback_keyword_search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Fast, robust keyword-scoring retrieval fallback when embedding model is unavailable."""
        import re

        if not self.chunks:
            return []

        query_words = set(re.findall(r'\w+', query.lower()))
        stop_words = {
            "what", "are", "your", "is", "the", "a", "an", "i", "need", "to",
            "how", "can", "in", "on", "of", "for", "and", "or", "me", "my", "do",
        }
        meaningful_words = query_words - stop_words
        words_to_use = meaningful_words if meaningful_words else query_words

        scored_chunks = []
        for chunk in self.chunks:
            text = chunk.get("text", "")
            text_lower = text.lower()
            score = sum(text_lower.count(word) for word in words_to_use)
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "text": chunk.get("text", ""),
                "source": chunk.get("source", ""),
                "score": float(score),
            }
            for score, chunk in scored_chunks[:top_k]
        ]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Retrieve top-k most relevant chunks for a query using vector or keyword search."""
        if top_k <= 0:
            return []

        # Ensure chunks are loaded (even if FAISS index is not)
        if not self.chunks:
            self.load_index()
            if not self.chunks and self.metadata_path.exists():
                try:
                    with self.metadata_path.open("r", encoding="utf-8") as f:
                        self.chunks = json.load(f)
                except Exception as e:
                    logger.warning("Could not load chunk metadata: %s", e)

        # 1. Try vector retrieval if index and embedding model are functional
        if self.index is not None and self.chunks:
            try:
                query_embedding = embedding_model.embed_query(query)
                if query_embedding is not None and query_embedding.size > 0:
                    k = min(top_k, len(self.chunks))
                    scores, indices = self.index.search(
                        np.asarray(query_embedding, dtype=np.float32), k
                    )
                    results: list[dict[str, Any]] = []
                    for score, idx in zip(scores[0], indices[0]):
                        if idx < 0 or idx >= len(self.chunks):
                            continue
                        chunk = self.chunks[idx]
                        results.append(
                            {
                                "text": chunk.get("text", ""),
                                "source": chunk.get("source", ""),
                                "score": float(score),
                            }
                        )
                    if results:
                        return results
            except Exception as e:
                logger.warning("Vector search failed (%s), falling back to keyword search", e)

        # 2. Fallback to keyword-based retrieval
        return self._fallback_keyword_search(query, top_k)


vector_store = VectorStore()

