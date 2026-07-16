from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime, timedelta
from app.core.database import get_db_session
from app.models.models import AccessLog, Vehicle, Camera
from app.api.auth import get_current_user
from app.services.redis_service import redis_service

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    # Today range
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Counts using SQLAlchemy queries
    in_today = await db.scalar(
        select(func.count(AccessLog.id)).filter(AccessLog.timestamp >= today_start, AccessLog.direction == "IN")
    )
    out_today = await db.scalar(
        select(func.count(AccessLog.id)).filter(AccessLog.timestamp >= today_start, AccessLog.direction == "OUT")
    )
    
    auth_vehicles = await db.scalar(
        select(func.count(Vehicle.id)).filter(Vehicle.status == "AUTHORIZED", Vehicle.is_active == True)
    )
    unauth_vehicles = await db.scalar(
        select(func.count(Vehicle.id)).filter(Vehicle.status == "UNAUTHORIZED")
    )
    pending_vehicles = await db.scalar(
        select(func.count(Vehicle.id)).filter(Vehicle.status == "PENDING")
    )
    
    active_cameras = await db.scalar(
        select(func.count(Camera.id)).filter(Camera.is_active == True)
    )

    # Simplified calculation for vehicle count inside: IN count minus OUT count
    inside_count = max(0, (in_today or 0) - (out_today or 0))

    # Health metrics (Placeholder stats, can be integrated via health checks)
    return {
        "today_in": in_today or 0,
        "today_out": out_today or 0,
        "inside_count": inside_count,
        "authorized_count": auth_vehicles or 0,
        "unauthorized_count": unauth_vehicles or 0,
        "pending_count": pending_vehicles or 0,
        "active_cameras": active_cameras or 0,
        "ai_status": "ONLINE",
        "database_status": "ONLINE",
        "redis_status": "ONLINE",
        "worker_status": "ONLINE"
    }

@router.get("/charts/hourly")
async def get_hourly_load(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    # Retrieve past 24 hours of traffic grouped by hour
    since_time = datetime.utcnow() - timedelta(hours=24)
    stmt = (
        select(
            func.extract("hour", AccessLog.timestamp).label("hour"),
            func.count(AccessLog.id).label("count")
        )
        .filter(AccessLog.timestamp >= since_time)
        .group_by("hour")
        .order_by("hour")
    )
    result = await db.execute(stmt)
    data = [{"hour": int(row[0]), "count": row[1]} for row in result.all()]
    return data
