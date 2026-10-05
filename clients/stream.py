"""Observe actual NDJSON events: an HTTP 200 does not prove completion."""

import json
import time
import httpx
from clients.common import BASE_URL, headers_for

CALLER = "dispatch"  # Choose a label from your current clients/common.py mapping.

BODY = {
    "question": "Which filter and airflow checks are documented?",
    "equipment_id": "EQ-FC-1002",
}


def main():
    started = time.perf_counter()
    terminal = None
    with httpx.stream(
        "POST",
        BASE_URL + "/v1/diagnose-stream",
        headers=headers_for(CALLER),
        json=BODY,
        timeout=90,
    ) as response:
        print(
            "Status:",
            response.status_code,
            "Request ID:",
            response.headers.get("x-request-id"),
        )
        if "application/x-ndjson" not in response.headers.get("content-type", ""):
            response.read()
            print(response.json())
            return
        for line in response.iter_lines():
            if not line:
                continue
            event = json.loads(line)
            print(f"{time.perf_counter() - started:.2f}s", event, flush=True)
            if event["type"] in {"complete", "error"}:
                terminal = event["type"]
    print("Terminal outcome:", terminal or "incomplete: no terminal event received")


if __name__ == "__main__":
    main()
