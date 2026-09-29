"""Formatting only: HTTP calls and assertions stay visible in notebooks."""
import json


def show_response(response) -> None:
    """Print status/body, never request headers or secret-bearing URLs."""
    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(response.text)
