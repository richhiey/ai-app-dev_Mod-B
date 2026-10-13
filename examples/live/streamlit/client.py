"""Visible UI-to-service boundary for the independent Live lab.

No model SDK or provider credential is used in this module.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

import httpx

HERE = Path(__file__).resolve().parent
QUESTION = "What belongs in a useful meeting note?"
CONTEXT = "A useful meeting note states the decision, names its owner, and records the next action."


def make_input(question, context):
    question = question.strip()
    if not question:
        raise ValueError("Enter a question before sending.")
    if len(question) > 2000 or len(context.strip()) > 4000:
        raise ValueError("Use at most 2000 question characters and 4000 context characters.")
    body = {"question": question}
    if context.strip():
        body["context"] = context.strip()
    return body


def demo_events(body, scenario="Success"):
    """Authored event examples. They never issue HTTP or call a provider."""
    if not body.get("context"):
        yield {"type": "response", "status": "needs_context", "answer": None,
               "references": [], "origin": "Demo"}
        return
    yield {"type": "metadata", "references": ["provided_context"], "mode": "demo"}
    yield {"type": "delta", "text": "DEMO: A useful note states the decision "}
    if scenario == "Interrupted":
        yield {"type": "error", "category": "demo_interrupted"}
    else:
        yield {"type": "delta", "text": "and names its owner."}
        yield {"type": "complete"}


def service_events(body, *, settings_path=None):
    """Read NDJSON events or ordinary JSON; return safe failure categories."""
    path = Path(settings_path) if settings_path else HERE / ".private" / "ui.json"
    try:
        settings = json.loads(path.read_text())
        base_url = settings["base_url"]
        url = urlparse(base_url)
        if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost") or url.username or url.password:
            raise ValueError("This classroom lab accepts a loopback HTTP service only.")
        headers = {"X-API-Key": settings["caller_key"]}
    except (OSError, ValueError, KeyError):
        yield {"type": "error", "category": "private_settings_unavailable"}
        return
    terminal = False
    try:
        with httpx.stream("POST", base_url.rstrip("/") + "/v1/answer-stream",
                          json=body, headers=headers, timeout=60) as response:
            yield {"type": "connection", "request_id": response.headers.get("x-request-id"),
                   "http_status": response.status_code, "target": base_url}
            if response.status_code != 200:
                yield {"type": "error", "category": {401: "unauthorized", 422: "invalid_request",
                        429: "rate_limited"}.get(response.status_code, "service_error"),
                       "retry_after": response.headers.get("retry-after")}
                return
            if "application/x-ndjson" not in response.headers.get("content-type", ""):
                response.read()
                value = response.json()
                if value.get("status") not in ("ready", "needs_context"):
                    raise ValueError("Unexpected JSON response")
                yield {**value, "type": "response"}
                return
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if not isinstance(event, dict) or event.get("type") not in (
                    "metadata", "delta", "usage", "complete", "error"
                ):
                    raise ValueError("Unexpected stream event")
                if event["type"] == "delta" and not isinstance(event.get("text"), str):
                    raise ValueError("Invalid text event")
                yield event
                if event["type"] in ("complete", "error"):
                    terminal = True
                    break
        if not terminal:
            yield {"type": "error", "category": "missing_terminal_event"}
    except (httpx.HTTPError, ValueError):
        yield {"type": "error", "category": "connection_or_protocol_error"}


def new_turn(body, origin):
    return {"body": body, "origin": origin, "text": "", "state": "Waiting", "events": [],
            "request_id": None, "references": [], "model": None, "tokens": None,
            "http_status": None, "target": None, "mode": None, "error": None, "retry_after": None}


def apply_event(turn, event):
    """State transition visible to instructors; text arrival never sets Completed."""
    kind = event["type"]
    turn["events"].append(kind)
    if kind == "connection":
        for key in ("request_id", "http_status", "target"):
            turn[key] = event.get(key)
    elif kind == "metadata":
        turn["references"] = event.get("references", [])
        turn["mode"] = event.get("mode")
        turn["request_id"] = event.get("request_id", turn["request_id"])
    elif kind == "delta":
        turn["text"] += event["text"]
        turn["state"] = "Receiving"
    elif kind == "usage":
        turn["model"], turn["tokens"] = event.get("model"), event.get("tokens")
    elif kind == "complete":
        turn["state"] = "Completed"
    elif kind == "response":
        turn["text"] = event.get("answer") or "Please supply context with your question."
        turn["references"] = event.get("references", [])
        turn["state"] = "Needs context" if event.get("status") == "needs_context" else "Response received"
    elif kind == "error":
        turn["state"] = "Incomplete" if turn["text"] else "Failed"
        turn["error"], turn["retry_after"] = event.get("category"), event.get("retry_after")
    return turn
