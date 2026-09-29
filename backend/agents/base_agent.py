"""Base agent class with RAG context retrieval for all specialized agents."""

import logging
from abc import ABC, abstractmethod

from backend.rag.retriever import vector_store
from backend.llm_client import groq_client

import re

logger = logging.getLogger(__name__)


def clean_plain_text(text: str) -> str:
    """Ensure agent responses are clean plain text without markdown asterisks or bolding."""
    if not text:
        return ""
    # Strip markdown bold: **text** -> text
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Strip any remaining double asterisks
    cleaned = cleaned.replace('**', '')
    # Strip markdown italic asterisks: *text* -> text
    cleaned = re.sub(r'(?<!\*)\*([^\*\n]+?)\*(?!\*)', r'\1', cleaned)
    # Strip any stray markdown header hashes: ### Title -> Title
    cleaned = re.sub(r'^\s*#{1,6}\s+', '', cleaned, flags=re.MULTILINE)
    # Convert leading bullet asterisks: * item -> - item
    cleaned = re.sub(r'^\s*\*\s+', '- ', cleaned, flags=re.MULTILINE)
    # Strip double underscores bolding: __text__ -> text
    cleaned = re.sub(r'__(.*?)__', r'\1', cleaned)
    return cleaned.strip()


# Style instruction appended to every agent's system prompt
CONCISE_STYLE_INSTRUCTION = (
    "\n\nStyle & Formatting Guidelines:\n"
    "- Keep responses concise, clear, and easy to interpret (under 100-150 words).\n"
    "- Output in plain text only. NEVER use markdown asterisks (no ** or *), bolding, or header hashes (#).\n"
    "- Use simple hyphens (-) or numbered steps (1., 2.) for lists, with clean plain text title lines.\n"
    "- Avoid long walls of text, fluff, and unnecessary preambles.\n"
    "- If asking for user details, ask for only 1 or 2 essential items directly."
)

# Boundary instruction — prevents off-topic usage
SCOPE_BOUNDARY_INSTRUCTION = (
    "\n\nScope Boundary (STRICTLY FOLLOW):\n"
    "- You are ONLY a TechMart Electronics customer support assistant.\n"
    "- You must ONLY answer questions related to TechMart products, orders, billing, "
    "technical support, policies, and company information.\n"
    "- If the user asks general/off-topic questions (e.g., career advice, recipes, "
    "homework help, personal chat like 'how are you?', 'what did you eat?', "
    "'tell me a joke', 'write me an essay'), politely decline and redirect:\n"
    '  Reply: "I\'m TechMart\'s support assistant and can only help with TechMart-related '
    "queries — orders, billing, products, or technical issues. How can I assist you with those?\"\n"
    "- NEVER act as a general-purpose AI chatbot."
)


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
        try:
            chunks = vector_store.retrieve(query, top_k=3)
        except Exception as e:
            logger.warning("RAG context retrieval failed for '%s': %s", query, e)
            chunks = []

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

        augmented_prompt = (
            f"{self.system_prompt}"
            f"{CONCISE_STYLE_INSTRUCTION}"
            f"{SCOPE_BOUNDARY_INSTRUCTION}"
            f"\n\nContext:\n{context}"
        )

        response_text = groq_client.chat(
            system_prompt=augmented_prompt,
            user_message=user_message,
            conversation_history=conversation_history,
            temperature=0.3,
            max_tokens=350,
        )

        response_text = clean_plain_text(response_text)

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
