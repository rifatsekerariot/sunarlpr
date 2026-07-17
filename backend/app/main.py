import os
import structlog
import asyncio
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
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
from app.api.settings import router as settings_router

setup_logging()
logger = structlog.get_logger()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

async def redis_listener(app: FastAPI):
    # Wait until redis is connected in lifespan
    await asyncio.sleep(1)
    client = await redis_service.get_client()
    pubsub = client.pubsub()
    await pubsub.subscribe("lpr_events")
    logger.info("Subscribed to Redis channel: lpr_events")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = message.get("data")
                if data:
                    await manager.broadcast(data)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info("Redis listener task cancelled")
    except Exception as e:
        logger.error("Error in Redis listener task", error=str(e))
    finally:
        await pubsub.unsubscribe("lpr_events")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Starting up FastAPI application")
    # Ensure media directory exists
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    await redis_service.connect()
    app.state.redis_listener_task = asyncio.create_task(redis_listener(app))
    yield
    # Shutdown tasks
    logger.info("Shutting down FastAPI application")
    if hasattr(app.state, "redis_listener_task"):
        app.state.redis_listener_task.cancel()
        try:
            await app.state.redis_listener_task
        except asyncio.CancelledError:
            pass
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
app.include_router(settings_router, prefix="/api")

@app.get("/health")
async def health_check():
    from datetime import datetime, timezone
    logger.info("Health check endpoint hit")
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection, wait for message or disconnection
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
