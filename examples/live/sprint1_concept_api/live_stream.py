"""LS09 composition: register the stream route before applying the guard."""

from .live_versions import app
from .stream_routes import router as stream_router

app.include_router(stream_router)

from .security_settings import CALLER_ENV
from module_b.security import LimitPolicy, SecurityMiddleware, protected_post_paths

app.add_middleware(SecurityMiddleware, caller_env=CALLER_ENV,
                   protected_paths=protected_post_paths(app),
                   policy=LimitPolicy(allowance=2, window_seconds=60))
