"""Text chunking utilities for document segmentation in the RAG pipeline."""

from __future__ import annotations

import logging
import re

from backend.config import settings

logger = logging.getLogger(__name__)


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-like units using punctuation and newlines as boundaries."""
    normalized = re.sub(r"\s+", " ", text.replace("\r", "\n")).strip()
    if not normalized:
        return []

    parts = re.split(r"(?<=[.!?])\s+|\n+", normalized)
    return [part.strip() for part in parts if part and part.strip()]


def chunk_text(text: str, source: str) -> list[dict[str, str]]:
    """Split text into overlapping chunks without breaking sentence boundaries where possible."""
    if not text.strip():
        return []

    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    sentences = _split_into_sentences(text)

    if not sentences:
        return []

    chunks: list[dict[str, str]] = []
    start_index = 0
    chunk_counter = 0

    while start_index < len(sentences):
        current_sentences: list[str] = []
        current_length = 0
        end_index = start_index

        while end_index < len(sentences):
            sentence = sentences[end_index]
            separator = 1 if current_sentences else 0
            projected_length = current_length + len(sentence) + separator

            if projected_length <= chunk_size or not current_sentences:
                current_sentences.append(sentence)
                current_length = projected_length
                end_index += 1
            else:
                break

        chunk_text_value = " ".join(current_sentences).strip()
        if chunk_text_value:
            chunks.append(
                {
                    "text": chunk_text_value,
                    "source": source,
                    "chunk_id": f"{source}_chunk_{chunk_counter}",
                }
            )
            chunk_counter += 1

        if end_index >= len(sentences):
            break

        if overlap <= 0:
            start_index = end_index
            continue

        rewind_chars = 0
        rewind_index = end_index
        while rewind_index > start_index and rewind_chars < overlap:
            rewind_index -= 1
            rewind_chars += len(sentences[rewind_index]) + 1

        start_index = rewind_index if rewind_index < end_index else end_index

    return chunks


def chunk_all_documents(documents: dict[str, str]) -> list[dict[str, str]]:
    """Create chunks for all documents and return a flat list of chunk metadata dictionaries."""
    all_chunks: list[dict[str, str]] = []

    for source, text in documents.items():
        chunks = chunk_text(text=text, source=source)
        all_chunks.extend(chunks)

    logger.info("Created %d chunks from %d documents", len(all_chunks), len(documents))
    return all_chunks
