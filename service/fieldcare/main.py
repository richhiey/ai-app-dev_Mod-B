"""Your service entry point. Register routes before attaching request guards."""

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fieldcare.config import openrouter_model
from fieldcare.resources import ServiceResources, index_prepared
from fieldcare.routes import router


@asynccontextmanager
async def lifespan(app):
    openrouter_model()  # Catch a model-name typo without contacting the provider.
    app.state.resources = ServiceResources()
    try:
        yield
    finally:
        app.state.resources.close()


app = FastAPI(title="FieldCare local service", lifespan=lifespan)
app.include_router(router)
# Register your additional routers here, before any middleware attachment.
# The authentication walkthrough shows the attachment to add below the routes.


@app.get("/health")
def health():
    """Process availability and preparation state; not proof of provider success."""
    return {
        "status": "ok",
        "index_prepared": index_prepared(),
        "provider_configured": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    }
