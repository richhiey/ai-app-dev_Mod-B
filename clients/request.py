"""Edit these three choices, predict the result, then run python -m clients.request."""

import httpx
from clients.common import BASE_URL, headers_for

CALLER = None
PATH = "/v1/diagnose"
BODY = {"question": "Which checks are documented?"}  # Missing equipment: clarification.


def main():
    response = httpx.post(
        BASE_URL + PATH, headers=headers_for(CALLER), json=BODY, timeout=90
    )
    print("Status:", response.status_code)
    print("Retry-After:", response.headers.get("retry-after"))
    print("Request ID:", response.headers.get("x-request-id"))
    print(response.json())


if __name__ == "__main__":
    main()
