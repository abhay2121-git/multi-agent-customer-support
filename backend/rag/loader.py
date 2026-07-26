"""Document loading utilities for the RAG knowledge base.

Supports both plain text (.txt) and PDF (.pdf) files.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def load_text_file(file_path: str) -> str:
    """Read a plain text file and return its contents."""
    path = Path(file_path)

    if not path.exists():
        logger.error("Text file not found: %s", path)
        return ""

    try:
        text = path.read_text(encoding="utf-8").strip()
        logger.info("Loaded text file %s (%d characters)", path.name, len(text))
        return text
    except Exception as exc:
        logger.error("Failed to read text file %s: %s", path.name, exc)
        return ""


def load_pdf(file_path: str) -> str:
    """Extract text from a single PDF file, handling encrypted or corrupted files gracefully."""
    path = Path(file_path)

    if not path.exists():
        logger.error("PDF file not found: %s", path)
        return ""

    try:
        reader = PdfReader(str(path))

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                logger.error("Could not decrypt encrypted PDF: %s", path.name)
                return ""

        page_count = len(reader.pages)
        pages_text: list[str] = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")

        text = "\n".join(pages_text).strip()
        logger.info("Loaded PDF %s with %d pages", path.name, page_count)
        return text
    except Exception as exc:
        logger.error("Failed to read PDF %s: %s", path.name, exc)
        return ""


def load_all_documents(knowledge_base_path: str) -> dict[str, str]:
    """Load all text and PDF documents from the knowledge base folder.

    Returns a filename-to-text mapping for all successfully loaded documents.
    Supports: .txt, .pdf
    """
    kb_path = Path(knowledge_base_path)

    if not kb_path.exists():
        logger.error("Knowledge base path not found: %s", kb_path)
        return {}

    documents: dict[str, str] = {}

    # Load .txt files
    for txt_path in sorted(kb_path.glob("*.txt")):
        extracted_text = load_text_file(str(txt_path))
        if extracted_text:
            documents[txt_path.name] = extracted_text

    # Load .pdf files
    for pdf_path in sorted(kb_path.glob("*.pdf")):
        extracted_text = load_pdf(str(pdf_path))
        if extracted_text:
            documents[pdf_path.name] = extracted_text

    total_characters = sum(len(text) for text in documents.values())
    logger.info(
        "Loaded %d documents (%d .txt, %d .pdf) with %d total characters",
        len(documents),
        len([k for k in documents if k.endswith(".txt")]),
        len([k for k in documents if k.endswith(".pdf")]),
        total_characters,
    )

    return documents
