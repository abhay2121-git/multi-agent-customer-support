"""Groq LLM client with smart retry logic and error classification."""

import logging
import time

from groq import Groq
from groq import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    APIConnectionError,
)
from backend.config import settings

logger = logging.getLogger(__name__)

# Exceptions that should NOT be retried (permanent failures)
_NON_RETRYABLE = (AuthenticationError, BadRequestError)

# Exceptions that SHOULD be retried (transient failures)
_RETRYABLE = (RateLimitError, APITimeoutError, InternalServerError, APIConnectionError)

# User-friendly messages
_MSG_AUTH_ERROR = (
    "AI service authentication failed. Please check the GROQ_API_KEY in your .env file."
)
_MSG_MODEL_ERROR = (
    "The configured AI model is invalid or unsupported. "
    "Check GROQ_MODEL in your .env file. Current value: '{}'"
)
_MSG_TRANSIENT_ERROR = (
    "The AI service is temporarily unavailable. Please try again in a moment."
)
_MSG_UNKNOWN_ERROR = (
    "An unexpected error occurred while contacting the AI service. "
    "Please try again or contact support."
)


class GroqClient:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.error(
                "GroqClient initialized without API key. "
                "Set GROQ_API_KEY in your .env file."
            )
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        logger.info("GroqClient initialized with model: %s", self.model)

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: list[dict] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        if conversation_history is None:
            conversation_history = []

        messages = [{"role": "system", "content": system_prompt}]

        recent_history = conversation_history[-6:]
        messages.extend(recent_history)

        messages.append({"role": "user", "content": user_message})

        return self._call_with_retry(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            method_name="chat",
        )

    def classify(self, prompt: str, options: list[str]) -> str:
        messages = [{"role": "user", "content": prompt}]
        result = self._call_with_retry(
            messages=messages,
            temperature=0.0,
            max_tokens=600,
            method_name="classify",
        )
        return result

    def _call_with_retry(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        method_name: str,
        max_retries: int = 3,
    ) -> str:
        """Execute a Groq API call with smart retry logic.

        Non-retryable errors (auth, bad request/model) fail immediately.
        Retryable errors (rate limit, timeout, server error) retry with exponential backoff.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                usage = response.usage
                if usage:
                    logger.info(
                        "Groq API usage [%s] — Prompt: %d, Completion: %d, Total: %d",
                        method_name,
                        usage.prompt_tokens,
                        usage.completion_tokens,
                        usage.total_tokens,
                    )

                msg = response.choices[0].message
                content = msg.content or ""

                # For reasoning models (e.g. gpt-oss): if content is empty, extract from reasoning
                if not content.strip() and hasattr(msg, "reasoning") and msg.reasoning:
                    import re
                    match = re.search(r'\[\s*"[^"]*"\s*(?:,\s*"[^"]*"\s*)*\]', msg.reasoning)
                    if match:
                        content = match.group(0)

                return content


            except AuthenticationError as e:
                logger.error(
                    "Groq authentication error [%s]: %s (NOT retrying)", method_name, e
                )
                return _MSG_AUTH_ERROR

            except (BadRequestError, NotFoundError) as e:
                error_msg = str(e)
                logger.error(
                    "Groq bad request/not found error [%s]: %s",
                    method_name,
                    error_msg,
                )
                if ("model" in error_msg.lower() or "not found" in error_msg.lower() or "decommissioned" in error_msg.lower()) and self.model != "openai/gpt-oss-20b":
                    logger.info("Attempting auto-fallback from '%s' to 'openai/gpt-oss-20b'...", self.model)
                    self.model = "openai/gpt-oss-20b"
                    try:
                        resp = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return resp.choices[0].message.content
                    except Exception as retry_err:
                        logger.error("Fallback to openai/gpt-oss-20b also failed: %s", retry_err)
                if "model" in error_msg.lower() or "not found" in error_msg.lower() or "decommissioned" in error_msg.lower():
                    return _MSG_MODEL_ERROR.format(self.model)
                return _MSG_UNKNOWN_ERROR


            except _RETRYABLE as e:
                wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s
                logger.warning(
                    "Groq transient error [%s] (attempt %d/%d): %s — retrying in %.1fs",
                    method_name,
                    attempt + 1,
                    max_retries,
                    e,
                    wait_time,
                )
                if attempt == max_retries - 1:
                    logger.error(
                        "Groq [%s] failed after %d retries: %s",
                        method_name,
                        max_retries,
                        e,
                    )
                    return _MSG_TRANSIENT_ERROR
                time.sleep(wait_time)

            except Exception as e:
                logger.error(
                    "Unexpected Groq error [%s] (attempt %d/%d): %s",
                    method_name,
                    attempt + 1,
                    max_retries,
                    e,
                    exc_info=True,
                )
                if attempt == max_retries - 1:
                    return _MSG_UNKNOWN_ERROR
                time.sleep(1)

        return _MSG_UNKNOWN_ERROR


groq_client = GroqClient()
