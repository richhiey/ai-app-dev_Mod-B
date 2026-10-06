"""LS03: retain existing routes, then register the separate pilot."""
from fieldcare.live_extension import app
from fieldcare.pilot_routes import router as pilot_router
app.include_router(pilot_router)
