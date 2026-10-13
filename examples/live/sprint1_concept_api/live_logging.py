"""LS10 learner starting file: attach observation after the existing guard."""

from .live_stream import app
from .config import work_dir
from .service import selected_model
from module_b.observability import ObservationMiddleware
from module_b.security import protected_post_paths

LOG_FIELDS = (
    "request_id", "route", "status_code", "outcome", "source",
    "configured_model", "model", "tokens", "latency_ms", "error_category",
)

# Add the supplied observation attachment here, using fields=LOG_FIELDS.
