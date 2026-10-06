"""Reviewed public Live composition; inspect before starting its own process."""
from fieldcare.live_versions import app
from module_b.security import SecurityMiddleware, protected_post_paths, LimitPolicy
from fieldcare.security_settings import CALLER_ENV
POLICY = LimitPolicy(allowance=2, window_seconds=60)
app.add_middleware(
    SecurityMiddleware,
    caller_env=CALLER_ENV,
    protected_paths=protected_post_paths(app),
    policy=POLICY,
)
