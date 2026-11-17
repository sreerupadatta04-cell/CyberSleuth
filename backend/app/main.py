from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models # Ensure all models are registered with SQLAlchemy metadata

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-Driven, LLM-Assisted Multi-Agent Cybersecurity Investigation Platform"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In dev, allow Vite dev server origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SPA No-Cache Middleware for HTML pages so browser always reloads fresh bundles
@app.middleware("http")
async def add_no_cache_for_html(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Include API Routers
from app.api.routes.health import router as health_router
from app.api.routes.telemetry import router as telemetry_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.response import router as response_router
from app.api.routes.reports import router as reports_router
from app.api.routes.demos import router as demos_router
from app.api.routes.settings import router as settings_router

app.include_router(health_router, prefix="/api", tags=["Health & Overview"])
app.include_router(telemetry_router, prefix="/api/telemetry", tags=["Telemetry"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Threat Detection & Alerts"])
app.include_router(investigations_router, prefix="/api/investigations", tags=["LangGraph Investigations"])
app.include_router(evidence_router, prefix="/api/evidence", tags=["Evidence & Graph"])
app.include_router(response_router, prefix="/api/response", tags=["Response Center"])
app.include_router(reports_router, prefix="/api/reports", tags=["Forensic Reports"])
app.include_router(demos_router, prefix="/api/demos", tags=["Demo Scenarios"])
app.include_router(settings_router, prefix="/api/settings", tags=["System Settings"])

# Mount frontend static distribution if built
from fastapi.staticfiles import StaticFiles
from pathlib import Path
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "project": "CyberSleuth",
            "description": "AI-Powered Multi-Agent Cybersecurity Investigation Platform",
            "status": "online",
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
