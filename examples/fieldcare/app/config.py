"""Configuration for the live FieldCare service."""

import os

from module_b.openrouter import CHAT_MODELS, DEFAULT_CHAT_MODEL


def openrouter_model() -> str:
    """Return the course-approved chat model configured for this service."""
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL).strip()
    if model not in CHAT_MODELS:
        raise RuntimeError("OPENROUTER_MODEL must use a course-approved model ID.")
    return model


def validate_configuration() -> None:
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        raise RuntimeError("Set OPENROUTER_API_KEY before starting FieldCare.")
    openrouter_model()
