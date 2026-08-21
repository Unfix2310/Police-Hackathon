"""Gujarat CCTV Intelligence Platform — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import engine, Base

from api.cameras import router as cameras_router
from api.observations import router as observations_router
from api.entities import router as entities_router
from api.search import router as search_router
from api.correlation import router as correlation_router
from api.investigation import router as investigation_router
from api.incidents import router as incidents_router
from api.cases import router as cases_router
from api.evidence import router as evidence_router
from api.alerts import router as alerts_router
from api.watchlists import router as watchlists_router
from api.analytics import router as analytics_router
from api.admin import router as admin_router
from api.websocket import router as websocket_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cctv_platform")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup, cleanup on shutdown."""
    logger.info("Starting Gujarat CCTV Intelligence Platform API...")

    # Import all models so Base.metadata knows about them
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")

    yield  # Application runs here

    logger.info("Shutting down API server...")
    await engine.dispose()


app = FastAPI(
    title="Gujarat CCTV Intelligence Platform",
    description="Statewide CCTV Intelligence Ecosystem for Gujarat Police — Hackathon MVP",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": str(exc.detail)}})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
    )


# --- Include Routers ---

API_PREFIX = "/api/v1"

app.include_router(cameras_router, prefix=API_PREFIX, tags=["Cameras"])
app.include_router(observations_router, prefix=API_PREFIX, tags=["Observations"])
app.include_router(entities_router, prefix=API_PREFIX, tags=["Entities"])
app.include_router(search_router, prefix=API_PREFIX, tags=["Search"])
app.include_router(correlation_router, prefix=API_PREFIX, tags=["Correlation"])
app.include_router(investigation_router, prefix=API_PREFIX, tags=["Investigation"])
app.include_router(incidents_router, prefix=API_PREFIX, tags=["Incidents"])
app.include_router(cases_router, prefix=API_PREFIX, tags=["Cases"])
app.include_router(evidence_router, prefix=API_PREFIX, tags=["Evidence"])
app.include_router(alerts_router, prefix=API_PREFIX, tags=["Alerts"])
app.include_router(watchlists_router, prefix=API_PREFIX, tags=["Watchlists"])
app.include_router(analytics_router, prefix=API_PREFIX, tags=["Analytics"])
app.include_router(admin_router, prefix=API_PREFIX, tags=["Admin"])
app.include_router(websocket_router, tags=["WebSocket"])


# --- Root Health Check ---

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — platform identity and health."""
    return {
        "platform": "Gujarat CCTV Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
    }
