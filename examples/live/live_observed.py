"""LS09/10: observation is added last, outside the existing guard."""
from fieldcare.live_stream import app
from module_b.observability import ObservationMiddleware
from module_b.security import protected_post_paths
from fieldcare.config import openrouter_model, openrouter_model_v2, work_dir
app.add_middleware(
    ObservationMiddleware,
    path=work_dir() / "requests.jsonl",
    routes=protected_post_paths(app),
    approved_models=(openrouter_model(), openrouter_model_v2()),
)
