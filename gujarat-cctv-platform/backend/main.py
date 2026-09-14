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
from api.interactions import router as interactions_router    # v4.1 dynamic entity layer
from api.anpr_test import router as anpr_test_router          # Isolated ANPR test lab


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
    
    # Auto-seed cameras if table is empty or needs update
    try:
        from database import async_session_maker
        from models.camera import Camera
        from models.enums import CameraStatus
        from sqlalchemy import select
        from simulator.camera_registry import fetch_sentinel_catalogue
        
        async with async_session_maker() as session:
            result = await session.execute(select(Camera).limit(5))
            existing_cams = result.scalars().all()
            # If empty, old IDs, or missing coordinates, seed fresh
            needs_seed = len(existing_cams) == 0 or not any(c.cam_id.startswith("cam") for c in existing_cams) or any(c.latitude is None for c in existing_cams)
            
            if needs_seed:
                logger.info("Seeding cameras from Sentinel catalogue...")
                cameras_data = await fetch_sentinel_catalogue()
                for cam_data in cameras_data:
                    camera = Camera(
                        cam_id=cam_data["cam_id"],
                        display_name=cam_data.get("display_name", cam_data["cam_id"]),
                        rtsp_url=cam_data.get("rtsp_url") or settings.get_rtsp_url(cam_data["cam_id"]),
                        web_url=cam_data.get("web_url") or cam_data.get("hls_url"),
                        latitude=cam_data.get("latitude") or cam_data.get("lat"),
                        longitude=cam_data.get("longitude") or cam_data.get("lng"),
                        direction_deg=0,
                        location_type=cam_data.get("location_type", "Junction"),
                        police_station=cam_data.get("police_station", "Unknown"),
                        district=cam_data.get("district", "Ahmedabad"),
                        jurisdiction_code=cam_data.get("jurisdiction_code", "GJ-AHM"),
                        status=CameraStatus.ONLINE,
                    )
                    await session.merge(camera)
                await session.commit()
                logger.info(f"Successfully seeded {len(cameras_data)} Sentinel cameras into database.")
    except Exception as e:
        logger.error(f"Failed to seed cameras: {e}", exc_info=True)

    # Seed demo users if table is empty
    try:
        from models.user import User
        from models.watchlist import Watchlist, WatchlistEntry
        import hashlib
        
        def _hash_pw(pw: str) -> str:
            return hashlib.sha256(pw.encode()).hexdigest()
        
        async with async_session_maker() as session:
            result = await session.execute(select(User).limit(1))
            if not result.scalar_one_or_none():
                demo_users = [
                    User(
                        user_id="USR-001",
                        badge_number="GJ-OPR-001",
                        full_name="Demo Operator",
                        department="Traffic",
                        district="Ahmedabad",
                        police_station="Sabarmati",
                        jurisdiction_code="GJ-AHM",
                        role="operator",
                        password_hash=_hash_pw("demo123"),
                    ),
                    User(
                        user_id="USR-002",
                        badge_number="GJ-INV-001",
                        full_name="Demo Investigator",
                        department="CID",
                        district="Ahmedabad",
                        police_station="Sabarmati",
                        jurisdiction_code="GJ-AHM",
                        role="investigator",
                        password_hash=_hash_pw("demo123"),
                    ),
                    User(
                        user_id="USR-003",
                        badge_number="GJ-CMD-001",
                        full_name="Demo Commander",
                        department="Command Centre",
                        district="Ahmedabad",
                        police_station="HQ",
                        jurisdiction_code="GJ-AHM",
                        role="command",
                        password_hash=_hash_pw("demo123"),
                    ),
                    User(
                        user_id="USR-004",
                        badge_number="GJ-ADM-001",
                        full_name="Demo Administrator",
                        department="IT & Communications",
                        district="Gandhinagar",
                        police_station="State Police HQ",
                        jurisdiction_code="GJ-GND",
                        role="admin",
                        password_hash=_hash_pw("demo123"),
                    ),
                ]
                for u in demo_users:
                    await session.merge(u)
                await session.commit()
                logger.info("Seeded 4 demo users (operator/investigator/command/admin).")
            
            # Seed watchlist if empty
            result = await session.execute(select(Watchlist).limit(1))
            if not result.scalar_one_or_none():
                wl = Watchlist(
                    watchlist_id="WL-DEMO-001",
                    name="Demo Stolen Vehicles",
                    description="Seeded demo watchlist for hackathon demonstration",
                )
                await session.merge(wl)
                
                entries = [
                    WatchlistEntry(
                        entry_id="WLE-001",
                        watchlist_id="WL-DEMO-001",
                        entity_type="vehicle",
                        identifier_value="GJ-01-AB-1234",
                        attributes={"color": "white", "make": "Maruti", "model": "Swift", "class": "hatchback"},
                        status="ACTIVE",
                    ),
                    WatchlistEntry(
                        entry_id="WLE-002",
                        watchlist_id="WL-DEMO-001",
                        entity_type="vehicle",
                        identifier_value="GJ-05-CD-5678",
                        attributes={"color": "black", "make": "Hyundai", "model": "Creta", "class": "suv"},
                        status="ACTIVE",
                    ),
                ]
                for e in entries:
                    await session.merge(e)
                await session.commit()
                logger.info("Seeded demo watchlist with 2 vehicle entries.")
    except Exception as e:
        logger.error(f"Failed to seed demo users/watchlist: {e}", exc_info=True)
    
    # Initialize Stream Manager and pace stream loading
    try:
        from engine.stream_manager import get_stream_manager
        from simulator.camera_registry import fetch_sentinel_catalogue
        
        if not settings.SENTINEL_PASSWORD:
            logger.warning("SENTINEL_PASSWORD not configured — skipping RTSP stream workers. Set it in .env to enable live inference.")
        else:
            manager = get_stream_manager()
            cameras = await fetch_sentinel_catalogue()
            
            # Initialize inference workers for active cameras (scalable up to MAX_ACTIVE_STREAMS)
            max_streams = getattr(settings, "MAX_ACTIVE_STREAMS", 30)
            target_cameras = cameras[:max_streams] if max_streams > 0 else cameras
            started_count = 0
            for cam in target_cameras:
                if "rtsp_url" in cam and cam["rtsp_url"]:
                    await manager.start_stream(
                        camera_id=cam["cam_id"],
                        rtsp_url=cam["rtsp_url"],
                        target_fps=settings.FRAME_SAMPLE_RATE,  # 2 FPS
                        fallback_url=cam.get("hls_url")
                    )
                    started_count += 1
                    # Stagger worker starts to avoid flooding the thread pool
                    if started_count % 5 == 0:
                        await asyncio.sleep(0.5)
            logger.info(f"Started {started_count} Sentinel camera stream workers across {len(cameras)} registered cameras (RTSP over TCP with HLS fallback).")
    except Exception as e:
        logger.error(f"Failed to start stream manager: {e}", exc_info=True)

    yield  # Application runs here

    logger.info("Shutting down API server...")
    try:
        from engine.stream_manager import get_stream_manager
        manager = get_stream_manager()
        await manager.stop_all()
    except Exception as e:
        pass
    
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
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
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
app.include_router(interactions_router, prefix=API_PREFIX, tags=["Interactions & Hypotheses"])
app.include_router(anpr_test_router, prefix=API_PREFIX, tags=["ANPR Test Lab"])
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
