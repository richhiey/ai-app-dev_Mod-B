"""LS02: same registration added to main.py in local Campus work."""
from fieldcare.main import app
from fieldcare.brief_routes import router as brief_router
app.include_router(brief_router)
