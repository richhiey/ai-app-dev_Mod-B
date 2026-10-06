"""The OpenRouter boundary used by the FieldCare generation node."""

import json

from module_b.openrouter import OpenRouterClient, OpenRouterError


class ModelUnavailable(Exception):
    """A safe error category for callers; provider details stay server-side."""


def generate_answer(
    question: str,
    equipment: dict,
    documents: list[dict],
    *,
    system_prompt: str,
    model_name: str,
    client: OpenRouterClient,
) -> tuple[str, dict | None, str | None]:
    evidence = {
        "equipment": equipment,
        "documents": [
            {"doc_id": row["doc_id"], "title": row["title"], "text": row["text"]}
            for row in documents
        ],
    }
    try:
        response = client.chat(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Question:\n"
                    + question
                    + "\n\nEquipment record and retrieved service evidence:\n"
                    + json.dumps(evidence, ensure_ascii=False),
                },
            ],
            model=model_name,
            temperature=0.2,
            max_tokens=350,
        )
    except OpenRouterError:
        raise ModelUnavailable from None

    if response.finish_reason != "stop" or not (response.content or "").strip():
        raise ModelUnavailable
    return response.content.strip(), response.usage, response.model
