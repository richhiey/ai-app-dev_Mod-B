"""LS05 composition: versioned concept routes behind caller authentication."""

from .live_versions import app
from .security_settings import CALLER_ENV
from module_b.security import SecurityMiddleware, protected_post_paths

app.add_middleware(SecurityMiddleware, caller_env=CALLER_ENV,
                   protected_paths=protected_post_paths(app), policy=None)
