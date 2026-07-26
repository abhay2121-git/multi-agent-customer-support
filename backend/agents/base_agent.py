"""Base agent class with RAG context retrieval for all specialized agents."""

import logging
from abc import ABC, abstractmethod

from backend.rag.retriever import vector_store
from backend.llm_client import groq_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain
        self.system_prompt = self.get_system_prompt()

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    def retrieve_context(self, query: str) -> tuple[str, list[dict]]:
        """Retrieve RAG context for a query.

        Returns a tuple of (context_string, raw_chunks) to avoid double retrieval.
        """
        chunks = vector_store.retrieve(query, top_k=3)
        if not chunks:
            return "No relevant context found.", []

        context_str = "Relevant Information:\n"
        for chunk in chunks:
            source = chunk.get("source", "Unknown Source")
            text = chunk.get("text", "")
            context_str += f"Source: {source}\n{text}\n\n"

        return context_str, chunks

    def respond(self, user_message: str, conversation_history: list[dict] = None) -> dict:
        if conversation_history is None:
            conversation_history = []

        # Single retrieval call — reuse for both context and sources
        context, chunks = self.retrieve_context(user_message)

        augmented_prompt = f"{self.system_prompt}\n\nContext:\n{context}"

        response_text = groq_client.chat(
            system_prompt=augmented_prompt,
            user_message=user_message,
            conversation_history=conversation_history,
            temperature=0.3,
            max_tokens=1000,
        )

        # Extract unique sources from the already-retrieved chunks
        sources = []
        for chunk in chunks:
            source = chunk.get("source", "Unknown Source")
            if source not in sources:
                sources.append(source)

        return {
            "response": response_text,
            "agent": self.name,
            "context_sources": sources,
        }
