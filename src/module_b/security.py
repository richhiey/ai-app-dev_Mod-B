"""Provided access/usage pattern for the single-process FieldCare teaching service.

No credential issuance, distributed quota, storage encryption or production claim.
The caller config is read when middleware is constructed, before lifespan startup.
"""
from dataclasses import dataclass
import hmac
import math
import os
import re
import threading
import time
from starlette.responses import JSONResponse

service_clock = time.monotonic


@dataclass(frozen=True)
class LimitPolicy:
    allowance: int
    window_seconds: float

    def __post_init__(self):
        if type(self.allowance) is not int or self.allowance < 1:
            raise ValueError("allowance must be a positive integer")
        if isinstance(self.window_seconds, bool) or not isinstance(self.window_seconds, (int, float)) or not math.isfinite(self.window_seconds) or self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive and finite")


class ConfigurationError(ValueError):
    """Safe to display: configuration names only, never their values."""


def load_callers(caller_env, environ=None):
    env = os.environ if environ is None else environ
    if not caller_env or any(not re.fullmatch(r"[a-z][a-z0-9_-]*", label) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", name) for label, name in caller_env.items()):
        raise ConfigurationError("Use caller labels and uppercase environment names.")
    values = {}
    for label, name in caller_env.items():
        value = env.get(name, "")
        if not isinstance(value, str) or not value or value != value.strip() or not value.isascii() or not value.isprintable() or value.startswith("<"):
            raise ConfigurationError(f"Set {name} to a non-placeholder value in the runtime environment.")
        if value in values.values():
            raise ConfigurationError("Caller keys must be distinct.")
        values[label] = value
    return values


def protected_post_paths(app):
    """Inventory static POST routes after ALL route registrations; refuse parameters.

    Recompute on restart if routes change. This course has static POST model routes.
    Other methods, mounts and WebSocket routes require a separate coverage design.
    """
    def walk(routes, prefix=""):
        for route in routes:
            original = getattr(route, "original_router", None)
            if original is not None:  # FastAPI 0.141 lazy include_router representation
                yield from walk(original.routes, prefix + route.include_context.prefix)
            elif "POST" in (getattr(route, "methods", None) or set()):
                yield prefix + route.path
    paths = tuple(sorted(set(walk(app.routes))))
    if not paths or any("{" in path for path in paths):
        raise ConfigurationError("Expected registered static POST routes.")
    return paths


class FixedWindowLimiter:
    """One first-admission-anchored window per authenticated label, across routes."""
    def __init__(self, policy, clock=None):
        self.policy = policy
        self.clock = clock or service_clock
        self._buckets = {}
        self._lock = threading.Lock()

    def admit(self, caller):
        with self._lock:
            now = self.clock()
            start, count = self._buckets.get(caller, (now, 0))
            if now - start >= self.policy.window_seconds:
                start, count = now, 0
            if count >= self.policy.allowance:
                return False, max(1, math.ceil(self.policy.window_seconds - (now - start)))
            self._buckets[caller] = (start, count + 1)
            return True, 0


class SecurityMiddleware:
    """Authenticate, then optionally count, then enter validation and the handler.

    Missing/wrong/duplicate key: 401 and no allowance consumed. Authenticated
    admitted attempts count, including 422/502/clarification. Rejections: 429 with
    Retry-After seconds, no adapter call, no further increment. No remote reset.
    """
    def __init__(self, app, *, caller_env, protected_paths, policy=None, clock=None):
        self.app = app
        self._callers = load_callers(caller_env)
        self.paths = frozenset(protected_paths)
        if not self.paths or any(not isinstance(p, str) or not p.startswith("/") or "{" in p for p in self.paths):
            raise ConfigurationError("Supply the nonempty static protected path inventory.")
        if policy is not None and not isinstance(policy, LimitPolicy):
            raise ConfigurationError("Use LimitPolicy or None.")
        self.limiter = FixedWindowLimiter(policy, clock) if policy else None

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or scope['path'] not in self.paths:
            return await self.app(scope, receive, send)
        supplied = [v for k, v in scope['headers'] if k.lower() == b'x-api-key']
        caller = None
        if len(supplied) == 1:
            for label, expected in self._callers.items():
                if hmac.compare_digest(supplied[0], expected.encode('ascii')):
                    caller = label
        if caller is None:
            response = JSONResponse({'detail': 'Missing or invalid API key.'}, status_code=401,
                                    headers={'WWW-Authenticate': 'ApiKey', 'Cache-Control': 'no-store'})
            return await response(scope, receive, send)
        scope.setdefault('state', {})['caller_id'] = caller
        if self.limiter:
            allowed, retry = self.limiter.admit(caller)
            if not allowed:
                response = JSONResponse({'detail': 'Caller allowance exhausted.'}, status_code=429,
                                        headers={'Retry-After': str(retry), 'Cache-Control': 'no-store'})
                return await response(scope, receive, send)
        return await self.app(scope, receive, send)
