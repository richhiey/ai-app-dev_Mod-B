"""LS10 learner starting file: attach observation after this existing guard."""
from fieldcare.live_stream import app
from fieldcare.config import openrouter_model, openrouter_model_v2, work_dir
from module_b.observability import ObservationMiddleware
from module_b.security import protected_post_paths

# Keep these fields; choose whether first_content_ms helps your investigation.
LOG_FIELDS = (
    "request_id", "route", "status_code", "outcome", "source",
    "configured_model", "model", "tokens", "latency_ms", "error_category",
)

# Add the supplied observation attachment here, using fields=LOG_FIELDS.
