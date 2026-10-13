"""LS09 observation composition: log safe request summaries outside the guard."""

from .live_stream import app
from .config import work_dir
from .service import selected_model
from module_b.observability import ObservationMiddleware
from module_b.security import protected_post_paths

app.add_middleware(ObservationMiddleware, path=work_dir() / "requests.jsonl",
                   routes=protected_post_paths(app),
                   approved_models=(selected_model(), selected_model("OPENROUTER_MODEL_V2")))
