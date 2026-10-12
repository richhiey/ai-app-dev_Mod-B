"""Supplied local HTTP client. Run only on the Streamlit server, never in a browser."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values


class FieldCareError(Exception):
    """Safe display message and correlation fields, without raw response bodies."""

    def __init__(self, message, *, status_code=None, request_id="", retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id
        self.retry_after = retry_after


def make_input(question: str, equipment_id: str = "") -> dict:
    question, equipment_id = question.strip(), equipment_id.strip()
    if not question or len(question) > 2000:
        raise FieldCareError("Enter a question of 1–2000 characters.")
    if len(equipment_id) > 64:
        raise FieldCareError("Use an equipment ID of at most 64 characters.")
    return {"question": question, **({"equipment_id": equipment_id} if equipment_id else {})}


def load_settings() -> tuple[str, str]:
    """Read this UI's private settings; do not load the service's provider key."""
    local = dotenv_values(Path(__file__).with_name(".env.local"))
    url = os.environ.get("FIELDCARE_SERVICE_URL", local.get("FIELDCARE_SERVICE_URL") or "")
    key = os.environ.get("FIELDCARE_CALLER_KEY", local.get("FIELDCARE_CALLER_KEY") or "")
    _validate_settings(url, key)
    return url.rstrip("/"), key


def _validate_settings(base_url: str, caller_key: str):
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError:
        raise FieldCareError("Check the local FieldCare URL in .env.local.") from None
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment or port == 0):
        raise FieldCareError("Use a local HTTP origin such as http://127.0.0.1:8001.")
    if not caller_key or not caller_key.strip() or "\n" in caller_key or "\r" in caller_key:
        raise FieldCareError("Configure the private FieldCare caller key in .env.local.")


def stream_diagnosis(payload: dict, *, base_url: str, caller_key: str):
    """Yield metadata/delta/complete/error/response/usage events; never auto-retry."""
    _validate_settings(base_url, caller_key)
    request_id = ""
    try:
        # Ignore proxy environment variables and redirects so the key stays local.
        with httpx.Client(timeout=httpx.Timeout(60, connect=5), trust_env=False,
                          follow_redirects=False) as client:
            with client.stream("POST", base_url.rstrip("/") + "/v1/diagnose-stream",
                               json=payload, headers={"X-API-Key": caller_key}) as response:
                request_id = response.headers.get("x-request-id", "")
                if response.status_code != 200:
                    messages = {
                        401: "FieldCare rejected the caller. Check the private caller mapping.",
                        422: "FieldCare rejected the input. Compare the fields with its schema.",
                        429: "The caller allowance is used. Wait before submitting again.",
                        503: "FieldCare is not ready. Check its local setup and document index.",
                    }
                    retry = response.headers.get("retry-after", "")
                    raise FieldCareError(messages.get(response.status_code, "FieldCare could not complete this request."),
                                         status_code=response.status_code, request_id=request_id,
                                         retry_after=int(retry) if retry.isdigit() else None)
                content_type = response.headers.get("content-type", "").split(";")[0]
                if content_type == "application/json":
                    result = json.loads(response.read())
                    if not isinstance(result, dict) or result.get("status") not in {"ready", "needs_clarification"}:
                        raise ValueError("Unexpected JSON response")
                    yield {"type": "response", "request_id": request_id, "response": result}
                    return
                if content_type != "application/x-ndjson":
                    raise ValueError("Unexpected stream content type")
                for line in response.iter_lines():
                    if not line.strip():
                        continue
                    if len(line) > 64000:
                        raise ValueError("Oversized event")
                    event = json.loads(line)
                    if not isinstance(event, dict) or event.get("type") not in {
                        "metadata", "delta", "complete", "error", "usage"
                    }:
                        raise ValueError("Unexpected event")
                    if event["type"] == "metadata":
                        event.setdefault("request_id", request_id)
                    yield event
                    if event["type"] in {"complete", "error"}:
                        return
                raise FieldCareError("The stream ended before completion. Any partial text is incomplete.",
                                     request_id=request_id)
    except httpx.TimeoutException:
        raise FieldCareError("FieldCare timed out. Any partial text is incomplete; retry explicitly when ready.",
                             request_id=request_id) from None
    except httpx.HTTPError:
        raise FieldCareError("Cannot reach FieldCare. Check the local service and URL, then submit again.",
                             request_id=request_id) from None
    except (ValueError, UnicodeError):
        raise FieldCareError("FieldCare returned an unreadable response. Any partial text is incomplete.",
                             request_id=request_id) from None
