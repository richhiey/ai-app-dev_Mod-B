import os
from pathlib import Path

from .service import selected_model


def work_dir():
    path = Path(os.environ.get("WORKSHOP_WORK_DIR", "var"))
    path.mkdir(parents=True, exist_ok=True)
    return path
