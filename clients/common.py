"""Load client settings without printing credentials."""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
BASE_URL = "http://127.0.0.1:8000"


def headers_for(caller="dispatch"):
    names = {"dispatch": "FIELDCARE_DISPATCH_KEY", "partner": "FIELDCARE_PARTNER_KEY"}
    if caller is None:
        return {}
    if caller == "wrong":
        return {"X-API-Key": "deliberately-unrecognized-test-value"}
    name = names[caller]
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Set {name} in .env. Restart this client after changing it.")
    return {"X-API-Key": value}
