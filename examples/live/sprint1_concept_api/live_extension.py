"""LS02 composition: the base route plus the supplied brief example."""

from .main import app
from .brief_routes import router as brief_router

app.include_router(brief_router)
