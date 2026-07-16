from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import os
from app.core.database import get_db_session
from app.repositories.repositories import CameraRepository, VehicleRepository, AccessLogRepository
from app.services.lpr_service import LPRService
from app.api.schemas import DetectionRequest, AccessLogResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])

# Shared API key from environment configuration
LPR_WORKER_API_KEY = os.getenv("LPR_WORKER_API_KEY", "ariot-lpr-worker-shared-secure-token-2026")

@router.get("", response_model=List[AccessLogResponse])
async def list_logs(
    plate_number: str | None = None,
    camera_id: UUID | None = None,
    direction: str | None = None,
    is_authorized: bool | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    repo = AccessLogRepository(db)
    return await repo.search_logs(
        plate_number=plate_number,
        camera_id=camera_id,
        direction=direction,
        is_authorized=is_authorized,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.post("/detect", response_model=AccessLogResponse, status_code=status.HTTP_201_CREATED)
async def process_detection(
    detection: DetectionRequest,
    x_api_key: str | None = Header(None, alias="X-API-KEY"),
    db: AsyncSession = Depends(get_db_session)
):
    # Verify shared key to prevent unauthorized logs posting
    if not x_api_key or x_api_key != LPR_WORKER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-KEY header."
        )

    camera_repo = CameraRepository(db)
    vehicle_repo = VehicleRepository(db)
    access_log_repo = AccessLogRepository(db)
    
    lpr_service = LPRService(camera_repo, vehicle_repo, access_log_repo)
    
    log_entry = await lpr_service.process_plate_detection(
        plate_number=detection.plate_number,
        camera_id=detection.camera_id,
        direction=detection.direction,
        ocr_confidence=detection.ocr_confidence,
        ai_confidence=detection.ai_confidence,
        snapshot_path=detection.snapshot_path,
        plate_crop_path=detection.plate_crop_path,
        review_needed=detection.review_needed
    )
    
    await db.commit()
    return log_entry

@router.get("/history/{plate_number}", response_model=List[AccessLogResponse])
async def get_history(
    plate_number: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    repo = AccessLogRepository(db)
    return await repo.get_vehicle_history(plate_number, limit=limit)
