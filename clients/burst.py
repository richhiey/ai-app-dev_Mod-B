"""Your ordered experiment. Keep one server process running throughout."""

import httpx
from clients.common import BASE_URL, headers_for

# Add your own rows: label, caller, path, body. Predict the admission effect first.
REQUESTS = []


def main():
    if not REQUESTS:
        raise SystemExit(
            "Add your predicted request sequence to REQUESTS before running."
        )
    with httpx.Client(base_url=BASE_URL, timeout=90) as client:
        for row in REQUESTS:
            response = client.post(
                row["path"], headers=headers_for(row["caller"]), json=row["body"]
            )
            print(
                row["label"],
                response.status_code,
                "Retry-After:",
                response.headers.get("retry-after"),
            )
            print(response.json())


if __name__ == "__main__":
    main()
