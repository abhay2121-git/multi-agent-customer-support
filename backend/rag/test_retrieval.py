"""Simple retrieval test script for validating FAISS RAG search results."""

from __future__ import annotations

import logging

from backend.rag.retriever import vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main() -> None:
    """Run a predefined retrieval test suite and print top-3 results for each query."""
    if not vector_store.load_index():
        print("FAISS index not found. Run python backend/rag/build_index.py first.")
        return

    queries = [
        "What is the refund policy?",
        "My device won't turn on",
        "How long does shipping take?",
        "What is covered under warranty?",
        "What is the price of a laptop?",
    ]

    for query in queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        results = vector_store.retrieve(query, top_k=3)

        if not results:
            print("No results found.")
            continue

        for i, result in enumerate(results, start=1):
            preview = str(result.get("text", "")).replace("\n", " ")
            if len(preview) > 200:
                preview = preview[:200] + "..."

            print(f"{i}. Source: {result.get('source', 'unknown')}")
            print(f"   Score: {result.get('score', 0.0):.4f}")
            print(f"   Text: {preview}")


if __name__ == "__main__":
    main()
