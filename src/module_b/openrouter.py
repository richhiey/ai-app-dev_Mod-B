"""Small Module B client for the course-approved OpenRouter endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from getpass import getpass
import os

import httpx

CHAT_MODELS = {
    "google/gemini-2.5-flash-lite",
    "google/gemini-2.5-flash",
    "google/gemini-3.1-flash-lite",
}
DEFAULT_CHAT_MODEL = "google/gemini-3.1-flash-lite"
EMBEDDING_MODEL = "google/gemini-embedding-001"
BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterError(RuntimeError):
    """Safe provider boundary error; never include credentials or raw payloads."""


@dataclass(frozen=True)
class ChatResponse:
    content: str | None
    model: str | None
    finish_reason: str | None
    usage: dict | None


def require_openrouter_key(*, prompt: bool = False) -> str:
    """Load the key from Colab Secrets or a hidden prompt without displaying it."""
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        try:
            from google.colab import userdata

            key = (userdata.get("OPENROUTER_API_KEY") or "").strip()
        except Exception:
            key = ""
    if not key and prompt:
        key = getpass("OpenRouter API key: ").strip()
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY in Colab Secrets or your local environment.")
    os.environ["OPENROUTER_API_KEY"] = key
    return key


class OpenRouterClient:
    """Make real chat-completion and embedding requests through OpenRouter."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 60.0,
        app_title: str = "Module B FieldCare",
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required before creating the client.")
        self.app_title = app_title
        self._http = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def chat(self, messages: list[dict], *, model: str, temperature: float, max_tokens: int) -> ChatResponse:
        if model not in CHAT_MODELS:
            raise OpenRouterError("The requested chat model is not enabled for this course.")
        payload = self._post(
            "/chat/completions",
            {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
        )
        try:
            choice = payload["choices"][0]
            return ChatResponse(
                content=choice["message"].get("content"),
                model=payload.get("model"),
                finish_reason=choice.get("finish_reason"),
                usage=payload.get("usage"),
            )
        except (KeyError, IndexError, TypeError):
            raise OpenRouterError("OpenRouter returned an unreadable chat response.") from None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = self._post("/embeddings", {"model": EMBEDDING_MODEL, "input": texts})
        try:
            rows = sorted(payload["data"], key=lambda row: row["index"])
            vectors = [[float(value) for value in row["embedding"]] for row in rows]
        except (KeyError, TypeError, ValueError):
            raise OpenRouterError("OpenRouter returned unreadable embeddings.") from None
        if len(vectors) != len(texts) or any(not vector for vector in vectors):
            raise OpenRouterError("OpenRouter returned an incomplete embedding batch.")
        return vectors

    def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            response = self._http.post(
                BASE_URL + endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-Title": self.app_title,
                },
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError):
            raise OpenRouterError("The OpenRouter request failed.") from None
        if not isinstance(result, dict):
            raise OpenRouterError("OpenRouter returned an unreadable response.")
        return result
