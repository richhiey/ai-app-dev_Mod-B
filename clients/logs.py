"""Find one safe terminal record by the request ID returned to your client."""

import json
import sys
from fieldcare.config import work_dir


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m clients.logs REQUEST_ID")
    path = work_dir() / "requests.jsonl"
    if not path.exists():
        raise SystemExit(
            "No request log yet. Attach observation middleware and send a POST request."
        )
    matches = [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    matches = [row for row in matches if row.get("request_id") == sys.argv[1]]
    if not matches:
        raise SystemExit(
            "No matching record. Check the ID and whether observation was attached for this run."
        )
    for row in matches:
        print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
