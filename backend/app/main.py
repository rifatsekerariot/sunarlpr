import os
import structlog
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import get_db_session
from app.services.redis_service import redis_service

# API routers
from app.api.auth import router as auth_router
from app.api.cameras import router as cameras_router
from app.api.vehicles import router as vehicles_router
from app.api.access_logs import router as access_logs_router
from app.api.stats import router as stats_router
from app.api.html_partials import router as html_router

setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Starting up FastAPI application")
    # Ensure media directory exists
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    await redis_service.connect()
    yield
    # Shutdown tasks
    logger.info("Shutting down FastAPI application")
    await redis_service.close()

app = FastAPI(
    title="License Plate Recognition System API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend and nginx routing
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "https://sunar.ariot.com.tr",
        "http://sunar.ariot.com.tr",
        "http://127.0.0.1",
        "http://200.97.171.59"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount shared snapshots/media directory to serve plate and vehicle snapshots
app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")

# Register Routers
app.include_router(auth_router, prefix="/api")
app.include_router(cameras_router, prefix="/api")
app.include_router(vehicles_router, prefix="/api")
app.include_router(access_logs_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(html_router, prefix="/api")

@app.get("/health")
async def health_check():
    from datetime import datetime, timezone
    logger.info("Health check endpoint hit")
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
