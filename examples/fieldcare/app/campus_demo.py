"""Runnable instructor examples. Learner app.main stays independently editable.

Run with: uvicorn app.campus_demo:create_app --factory
Read this file beside the Campus notebook: route registration precedes the guard,
and observation wraps the guard so rejected requests are visible too.
"""
import os

from fastapi import FastAPI

from app.config import openrouter_model
from app.main import health, lifespan
from app.routes import router
from app.campus_routes import brief_router, v2_router
from module_b.security import LimitPolicy, SecurityMiddleware, protected_post_paths
from module_b.observability import ObservationMiddleware

CALLER_ENV = {
    "dispatch": "FIELDCARE_DISPATCH_KEY",
    "partner": "FIELDCARE_PARTNER_KEY",
}


def create_app():
    """Build a fresh demonstration app; never patch or register into app.main."""
    sprint = int(os.environ.get("CAMPUS_SPRINT", "1"))
    if sprint not in (1, 2, 3):
        raise ValueError("CAMPUS_SPRINT must be 1, 2, or 3.")
    app = FastAPI(title="FieldCare Campus demonstration", lifespan=lifespan)
    app.add_api_route("/health", health, methods=["GET"])
    app.include_router(router)
    app.include_router(brief_router)
    app.include_router(v2_router)
    if sprint == 3:
        from app.stream_routes import router as stream_router
        app.include_router(stream_router)

    if sprint >= 2:
        allowance = int(os.environ.get("CAMPUS_ALLOWANCE", "0"))
        if allowance < 0:
            raise ValueError("CAMPUS_ALLOWANCE cannot be negative.")
        policy = None if allowance == 0 else LimitPolicy(
            allowance=allowance, window_seconds=60,
        )
        app.add_middleware(
            SecurityMiddleware,
            caller_env=CALLER_ENV,
            protected_paths=protected_post_paths(app),
            policy=policy,
        )

    if sprint == 3:
        # Last added = outermost: log auth/limit rejections as well as route work.
        app.add_middleware(
            ObservationMiddleware,
            path=os.environ["FIELDCARE_LOG_PATH"],
            routes=protected_post_paths(app),
            approved_models=(openrouter_model(),),
        )
    return app
