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


def approved_model(model, setting="model_name"):
    model = model.strip()
    if model not in CHAT_MODELS:
        raise ValueError(f"Choose a course-approved {setting} in .env.")
    return model


def openrouter_model():
    return approved_model(os.getenv("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL), "OPENROUTER_MODEL")


def openrouter_model_v2():
    # An unset pilot uses its own default, never the mutable v1 setting.
    return approved_model(os.getenv("OPENROUTER_MODEL_V2", DEFAULT_CHAT_MODEL), "OPENROUTER_MODEL_V2")
