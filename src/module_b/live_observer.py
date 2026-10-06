"""Small response reader for the optional Sprint 4 direct API observer.

HTTP calls stay visible in the notebook. This module neither starts a service nor
calls a model. A streamed delta is not evidence of provider provenance.
"""
import ipaddress
import json
import os
import time
from urllib.parse import urlsplit

import requests


def hosted_settings():
    """Read caller settings without echoing private values; work in Colab/Jupyter."""
    try:
        from google.colab import userdata
    except ImportError:
        values = [os.environ.get(name, "") for name in
                  ("FIELDCARE_SERVICE_URL", "FIELDCARE_CALLER_KEY")]
    else:
        try:
            values = [userdata.get(name) for name in
                      ("FIELDCARE_SERVICE_URL", "FIELDCARE_CALLER_KEY")]
        except Exception:
            raise RuntimeError("Add both caller settings in Colab Secrets and enable notebook access.") from None
    origin, key = (str(value or "").strip() for value in values)
    origin = origin.rstrip("/")
    parts = urlsplit(origin)
    if (parts.scheme != "https" or not parts.hostname or parts.path
            or parts.username or parts.password or parts.query or parts.fragment):
        raise ValueError("Use the facilitator's HTTPS origin without a path, query or credentials.")
    try:
        local = ipaddress.ip_address(parts.hostname).is_loopback
    except ValueError:
        local = parts.hostname.lower() == "localhost"
    if local:
        raise ValueError("Hosted Colab cannot use your laptop's localhost; use the local UI workflow instead.")
    if not key:
        raise ValueError("Provide FIELDCARE_CALLER_KEY privately; never paste it in a cell.")
    return origin, key


def empty_observation(label):
    return dict(label=label, http_status=None, request_id=None, content_type=None,
                application_status=None, mode=None, terminal_event=None,
                delta_count=0, first_content_ms=None, elapsed_ms=None, failure=None,
                retry_after=None)


def _event_lines(response, started, max_seconds):
    """Bound duration and bytes; tiny chunks expose small teaching streams promptly."""
    line = bytearray()
    total = 0
    for chunk in response.iter_content(chunk_size=1):
        if time.monotonic() - started > max_seconds:
            raise TimeoutError("Stream observation time budget exceeded")
        total += len(chunk)
        if total > 1_000_000:
            raise ValueError("Stream observation byte budget exceeded")
        line.extend(chunk)
        if len(line) > 65_536:
            raise ValueError("Event line exceeds the observation limit")
        if line.endswith(b"\n"):
            if line.strip():
                yield json.loads(line)
            line.clear()
    if line.strip():
        yield json.loads(line)


def observe_response(response, *, label, started=None, emit=print, max_seconds=90):
    """Read actual response semantics; never promote HTTP 200 to model success."""
    started = time.monotonic() if started is None else started
    record = empty_observation(label)
    record.update(http_status=response.status_code,
                  request_id=response.headers.get("X-Request-ID"),
                  content_type=response.headers.get("Content-Type", "").split(";")[0],
                  retry_after=response.headers.get("Retry-After"))
    try:
        if response.status_code != 200:
            emit(f"{label}: HTTP {response.status_code}; Retry-After={record['retry_after']}")
            return record
        if record["content_type"] == "application/json":
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Expected a response object")
            record.update(application_status=body.get("status"), mode=body.get("mode"))
            emit(f"{label}: JSON status={record['application_status']}, mode={record['mode']}")
            emit(body.get("answer", ""))
            return record
        if record["content_type"] != "application/x-ndjson":
            raise ValueError("Expected JSON or newline-delimited JSON")
        for event in _event_lines(response, started, max_seconds):
            if not isinstance(event, dict):
                raise ValueError("Expected an event object")
            kind = event.get("type")
            if kind == "metadata":
                event_id = event.get("request_id")
                if record["request_id"] and event_id and event_id != record["request_id"]:
                    raise ValueError("Header and metadata request IDs disagree")
                record.update(request_id=event_id or record["request_id"],
                              application_status=event.get("status"), mode=event.get("mode"))
                emit({key: event.get(key) for key in ("type", "mode", "request_id", "citations")})
            elif kind == "delta":
                piece = event.get("text")
                if not isinstance(piece, str):
                    raise ValueError("Expected text in a delta")
                if piece:
                    record["delta_count"] += 1
                    if record["first_content_ms"] is None:
                        record["first_content_ms"] = round((time.monotonic() - started) * 1000, 1)
                    emit(piece)
            elif kind in ("complete", "error"):
                event_id = event.get("request_id")
                if record["request_id"] and event_id and event_id != record["request_id"]:
                    raise ValueError("Terminal request ID disagrees")
                record["terminal_event"] = kind
                if kind == "error":
                    record["failure"] = "service_error_event"
                emit(f"Terminal event: {kind}")
                break
            elif kind == "usage":
                emit({key: event.get(key) for key in ("type", "model", "tokens")})
            else:
                raise ValueError("Unknown stream event")
        if record["terminal_event"] is None:
            record["failure"] = "incomplete_stream"
            emit("Connection ended without a terminal event: partial text is incomplete.")
    except (requests.RequestException, TimeoutError, ValueError, UnicodeError) as error:
        record["failure"] = type(error).__name__
        emit(f"{label}: observation failed ({type(error).__name__}); keep the partial result unfinished.")
    finally:
        record["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
    return record


def transport_failure(label, error):
    record = empty_observation(label)
    record["failure"] = type(error).__name__
    return record
