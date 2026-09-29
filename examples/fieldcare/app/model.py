"""The visible boundary between FieldCare and an external model provider."""
import json
import os

import httpx

from app.config import Mode


class ModelUnavailable(Exception):
    """A safe category; do not expose provider response bodies or credentials."""


def generate_answer(
    question: str, evidence: dict, *, system_prompt: str, model_name: str, mode: Mode
) -> str:
    if mode == "demo":
        return (
            "DEMO: No model was called. The supplied HX documents describe checking approved "
            "filter selection, orientation, gasket contact and panel seating, then recording "
            "the airflow reading. These are document-based checks, not a diagnosis of this unit. "
            "A qualified technician must verify the actual condition."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps({"question": question, "evidence": evidence})},
    ]
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            json={"model": model_name, "messages": messages, "temperature": 0.2, "max_tokens": 350},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        if payload["choices"][0].get("finish_reason") != "stop":
            raise ModelUnavailable("The provider did not return a complete answer.")
        answer = payload["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ModelUnavailable("The provider did not return text.")
        return answer.strip()
    except (httpx.HTTPError, KeyError, ValueError, IndexError, TypeError):
        raise ModelUnavailable("The provider call failed.") from None
