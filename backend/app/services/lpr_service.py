import structlog
from uuid import UUID
from datetime import datetime, timezone
from app.repositories.repositories import CameraRepository, VehicleRepository, AccessLogRepository
from app.models.models import Camera, Vehicle, AccessLog
from app.services.redis_service import redis_service

logger = structlog.get_logger()

class LPRService:
    def __init__(
        self,
        camera_repo: CameraRepository,
        vehicle_repo: VehicleRepository,
        access_log_repo: AccessLogRepository
    ):
        self.camera_repo = camera_repo
        self.vehicle_repo = vehicle_repo
        self.access_log_repo = access_log_repo

    async def process_plate_detection(
        self,
        plate_number: str,
        camera_id: UUID,
        direction: str,
        ocr_confidence: float,
        ai_confidence: float,
        snapshot_path: str,
        plate_crop_path: str,
        review_needed: bool = False
    ) -> AccessLog:
        logger.info("processing_plate_detection", plate=plate_number, camera_id=str(camera_id), review_needed=review_needed)

        # 1. Look up vehicle in database
        vehicle = await self.vehicle_repo.get_by_plate(plate_number)
        
        # Determine authorization state
        is_authorized = False
        status = "PENDING"
        
        if vehicle:
            status = vehicle.status
            if vehicle.status == "AUTHORIZED" and vehicle.is_active:
                if not vehicle.valid_until or vehicle.valid_until > datetime.now(timezone.utc):
                    is_authorized = True
        else:
            # First time seen: Auto create a PENDING (Bilinmeyen Araç) vehicle
            vehicle = Vehicle(
                plate_number=plate_number,
                status="PENDING",
                snapshot_path=snapshot_path,
                is_active=True
            )
            vehicle = await self.vehicle_repo.create(vehicle)
            status = "PENDING"

        # 2. Gate Opening Rule Check (decision logic done in python backend)
        gate_opened = False
        if is_authorized:
            gate_opened = True

        # 3. Create Access Log
        access_log = AccessLog(
            plate_number=plate_number,
            vehicle_id=vehicle.id,
            camera_id=camera_id,
            direction=direction,
            timestamp=datetime.now(timezone.utc),
            ocr_confidence=ocr_confidence,
            ai_confidence=ai_confidence,
            snapshot_path=snapshot_path,
            plate_crop_path=plate_crop_path,
            is_authorized=is_authorized,
            gate_opened=gate_opened,
            review_needed=review_needed
        )
        
        access_log = await self.access_log_repo.create(access_log)

        # 4. Publish Event to Redis (WebSocket subscriber in UI will catch this)
        camera_obj = await self.camera_repo.get_by_id(camera_id)
        camera_name = camera_obj.name if camera_obj else "Bilinmeyen Kamera"
        
        event_payload = {
            "event_type": "PLATE_DETECTED",
            "log_id": str(access_log.id),
            "plate_number": plate_number,
            "status": status,
            "camera_name": camera_name,
            "direction": direction,
            "timestamp": access_log.timestamp.isoformat(),
            "snapshot_path": snapshot_path,
            "ocr_confidence": ocr_confidence,
            "gate_opened": gate_opened
        }
        
        await redis_service.publish_event("lpr_events", event_payload)
        
        return access_log
