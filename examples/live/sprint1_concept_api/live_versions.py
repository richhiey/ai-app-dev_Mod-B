"""LS03 composition: base, learner extension and independent v2 example."""

from .live_extension import app
from .pilot_routes import router as pilot_router

app.include_router(pilot_router)
