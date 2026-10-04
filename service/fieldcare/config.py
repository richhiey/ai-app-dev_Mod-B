"""Local settings: paths are stable even when the shell's directory changes."""

import os
from pathlib import Path
from dotenv import load_dotenv
from module_b.openrouter import CHAT_MODELS, DEFAULT_CHAT_MODEL

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "service" / "data"
load_dotenv(ROOT / ".env", override=False)


def work_dir():
    path = Path(os.getenv("FIELDCARE_WORK_DIR", "var")).expanduser()
    return (path if path.is_absolute() else ROOT / path).resolve()


def openrouter_model():
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL).strip()
    if model not in CHAT_MODELS:
        raise ValueError("Choose a course-approved OPENROUTER_MODEL in .env.")
    return model
