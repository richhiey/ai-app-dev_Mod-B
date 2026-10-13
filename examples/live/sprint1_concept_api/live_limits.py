"""LS06 composition: two admissions per caller in a 60-second window."""

from .live_versions import app
from .security_settings import CALLER_ENV
from module_b.security import LimitPolicy, SecurityMiddleware, protected_post_paths

app.add_middleware(SecurityMiddleware, caller_env=CALLER_ENV,
                   protected_paths=protected_post_paths(app),
                   policy=LimitPolicy(allowance=2, window_seconds=60))
