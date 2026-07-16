from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.core.database import get_db_session
from app.repositories.repositories import CameraRepository
from app.api.schemas import CameraCreate, CameraResponse
from app.models.models import Camera
from app.api.auth import get_current_user

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    repo = CameraRepository(db)
    return await repo.get_all()

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_in: CameraCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to configure cameras")
    repo = CameraRepository(db)
    camera = Camera(**camera_in.model_dump())
    new_camera = await repo.create(camera)
    await db.commit()
    return new_camera

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: UUID,
    camera_in: CameraCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to update cameras")
    repo = CameraRepository(db)
    camera = await repo.update(camera_id, **camera_in.model_dump())
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    await db.commit()
    return camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admins can delete cameras")
    repo = CameraRepository(db)
    success = await repo.delete(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    await db.commit()
