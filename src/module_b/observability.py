"""Small allowlisted ASGI request summaries; no request/response bodies retained."""

import asyncio
import json
import math
import re
import time
import uuid
from pathlib import Path

FIELDS = (
    "request_id",
    "route",
    "status_code",
    "outcome",
    "source",
    "model",
    "tokens",
    "latency_ms",
    "first_content_ms",
    "error_category",
    "case_id",
)
OUTCOMES = {"completed", "failed", "rejected", "cancelled"}
ERRORS = {
    "none",
    "unauthorized",
    "rate_limited",
    "invalid_request",
    "provider_interrupted",
    "provider_incomplete",
    "provider_not_configured",
    "provider_rejected",
    "provider_unavailable",
    "internal_error",
    "client_disconnected",
}
SOURCES = {"none", "live_provider"}


def safe_record(values, *, fields=FIELDS, routes=()):
    """Minimize first. Nested values, arbitrary strings and unknown keys are dropped.

    This is an allowlist for this schema, not a universal personal-data detector.
    A provider model identifier is accepted only when equal to an approved value
    supplied through the dedicated trusted configuration, never from body/header.
    """
    out = {}
    for key in fields:
        if key not in FIELDS:
            continue
        value = values.get(key)
        if key == "request_id":
            try:
                value = str(uuid.UUID(value))
            except (ValueError, TypeError, AttributeError):
                continue
        elif key == "route":
            value = value if value in routes else "unmatched"
        elif key == "outcome":
            value = value if value in OUTCOMES else "failed"
        elif key == "source":
            value = value if value in SOURCES else "none"
        elif key == "error_category":
            value = value if value in ERRORS else "internal_error"
        elif key == "case_id":
            value = (
                value
                if isinstance(value, str)
                and re.fullmatch(r"EVAL-FC-0(?:0[1-9]|1[0-6])", value)
                else None
            )
        elif key == "model":
            approved = values.get("_approved_models", ())
            value = value if isinstance(value, str) and value in approved else None
        elif key == "status_code":
            value = value if type(value) is int and 100 <= value <= 599 else None
        elif key == "tokens":
            value = value if type(value) is int and value >= 0 else None
        else:
            value = (
                round(value, 2)
                if type(value) in (int, float) and math.isfinite(value) and value >= 0
                else None
            )
        out[key] = value
    return out


class ObservationMiddleware:
    """One terminal record per POST. Install OUTSIDE authentication/limiting.

    Disconnection is determined from receive/cancellation/send failure, never from
    counting content chunks. Client abort is observable, but completed can win a
    race after the entire response has already been sent.
    """

    def __init__(self, app, *, path, routes, fields=FIELDS, approved_models=()):
        self.app = app
        self.path = Path(path)
        self.routes = tuple(routes)
        self.fields = tuple(fields)
        self.approved_models = tuple(approved_models)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        start = time.perf_counter()
        state = scope.setdefault("state", {})
        state["request_id"] = str(uuid.uuid4())
        state["observation"] = {
            "source": "none",
            "model": None,
            "tokens": None,
            "error_category": "none",
        }
        status = 500
        complete = False
        disconnected = False

        async def safe_receive():
            nonlocal disconnected
            message = await receive()
            if message["type"] == "http.disconnect":
                disconnected = True
            return message

        async def safe_send(message):
            nonlocal status, complete
            if message["type"] == "http.response.start":
                status = message["status"]
                # A streaming route can already set this header. Emit one
                # authoritative value, otherwise clients join duplicates with a
                # comma and no longer match the terminal record's UUID.
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != b"x-request-id"
                ]
                message = {
                    **message,
                    "headers": headers
                    + [(b"x-request-id", state["request_id"].encode())],
                }
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                complete = True
            await send(message)

        try:
            await self.app(scope, safe_receive, safe_send)
        except asyncio.CancelledError:
            disconnected = True
            raise
        except Exception:
            state["observation"]["error_category"] = "internal_error"
            if not complete:
                # No raw exception details reach our log. Framework output is disabled
                # by the owned runtime; callers see a safe generic failure.
                raise RuntimeError("Service request failed") from None
        finally:
            observation = state["observation"]
            error = observation.get("error_category", "none")
            if disconnected and not complete:
                outcome = "cancelled"
                error = "client_disconnected"
            elif status >= 400:
                outcome = "rejected" if status < 500 else "failed"
                error = {
                    401: "unauthorized",
                    429: "rate_limited",
                    422: "invalid_request",
                }.get(status, "internal_error")
            elif not complete or error != "none":
                outcome = "failed"
            else:
                outcome = "completed"
            values = {
                **observation,
                "request_id": state["request_id"],
                "route": scope["path"],
                "status_code": status,
                "outcome": outcome,
                "error_category": error,
                "latency_ms": (time.perf_counter() - start) * 1000,
                "_approved_models": self.approved_models,
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as stream:
                stream.write(
                    json.dumps(
                        safe_record(values, fields=self.fields, routes=self.routes)
                    )
                    + "\n"
                )
