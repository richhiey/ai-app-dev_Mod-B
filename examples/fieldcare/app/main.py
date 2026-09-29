"""Start with: python -m uvicorn app.main:app --env-file .env --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_mode, validate_configuration
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_configuration()
    yield


app = FastAPI(title="FieldCare service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    """Process readiness only; this does not make a provider call."""
    return {"status": "ok", "mode": get_mode()}
