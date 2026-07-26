"""Standalone script to build the RAG FAISS index from knowledge base documents."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path when run as a script
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.rag.chunker import chunk_all_documents
from backend.rag.loader import load_all_documents
from backend.rag.retriever import vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main() -> None:
    """Build the vector index from knowledge base documents and print pipeline summary."""
    start = time.time()

    # Resolve knowledge_base path relative to project root
    kb_path = Path(project_root) / "knowledge_base"
    if not kb_path.exists():
        print(f"ERROR: Knowledge base directory not found: {kb_path}")
        print("Create a 'knowledge_base/' directory and add .txt or .pdf files.")
        sys.exit(1)

    print(f"Loading documents from: {kb_path}")
    documents = load_all_documents(str(kb_path))

    if not documents:
        print("No documents found. Ensure knowledge_base/ contains .txt or .pdf files.")
        sys.exit(1)

    print(f"Documents loaded: {len(documents)}")
    for name in documents:
        print(f"  - {name} ({len(documents[name])} chars)")

    chunks = chunk_all_documents(documents)

    if not chunks:
        print("No chunks generated from documents.")
        sys.exit(1)

    vector_store.build_index(chunks)

    elapsed = time.time() - start
    index_size = vector_store.index.ntotal if vector_store.index else 0

    print("\n" + "=" * 50)
    print("RAG Index Build — Complete")
    print("=" * 50)
    print(f"  Documents loaded : {len(documents)}")
    print(f"  Chunks created   : {len(chunks)}")
    print(f"  Index vectors    : {index_size}")
    print(f"  Index file       : {vector_store.index_path}")
    print(f"  Metadata file    : {vector_store.metadata_path}")
    print(f"  Total time       : {elapsed:.2f}s")
    print("=" * 50)


if __name__ == "__main__":
    main()
