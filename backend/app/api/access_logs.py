from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.core.database import get_db_session
from app.repositories.repositories import CameraRepository, VehicleRepository, AccessLogRepository
from app.services.lpr_service import LPRService
from app.api.schemas import DetectionRequest, AccessLogResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/access-logs", tags=["Access Logs"])

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
    db: AsyncSession = Depends(get_db_session)
):
    # This endpoint is called by the camera-worker, it runs without user JWT token but from local container network
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
        plate_crop_path=detection.plate_crop_path
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
