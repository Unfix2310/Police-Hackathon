from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

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

app = FastAPI(title="Gujarat CCTV Intelligence Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Backend failure"}}
    )

api_prefix = "/api/v1"
app.include_router(cameras_router, prefix=api_prefix)
app.include_router(observations_router, prefix=api_prefix)
app.include_router(entities_router, prefix=api_prefix)
app.include_router(search_router, prefix=api_prefix)
app.include_router(correlation_router, prefix=api_prefix)
app.include_router(investigation_router, prefix=api_prefix)
app.include_router(incidents_router, prefix=api_prefix)
app.include_router(cases_router, prefix=api_prefix)
app.include_router(evidence_router, prefix=api_prefix)
app.include_router(alerts_router, prefix=api_prefix)
app.include_router(watchlists_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)

# Admin has some endpoints that belong to /api/v1
app.include_router(admin_router, prefix=api_prefix)

# WebSocket routes are defined with full paths in the router
app.include_router(websocket_router)

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up API server...")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutting down API server...")
