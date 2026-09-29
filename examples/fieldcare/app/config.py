"""Read settings; never print credentials or silently switch live mode to demo."""
import os
from typing import Literal

Mode = Literal["demo", "live"]


def get_mode() -> Mode:
    mode = os.getenv("FIELDCARE_MODE", "demo").strip()
    if mode not in ("demo", "live"):
        raise RuntimeError("FIELDCARE_MODE must be demo or live.")
    return mode


def validate_configuration() -> None:
    if get_mode() == "live":
        required = ("OPENROUTER_API_KEY", "OPENROUTER_MODEL")
        if any(not os.getenv(name, "").strip() for name in required):
            raise RuntimeError("Live mode requires OPENROUTER_API_KEY and OPENROUTER_MODEL.")
