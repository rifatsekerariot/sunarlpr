from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import asyncio
import re
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


def _parse_rtsp_host_port(rtsp_url: str):
    """Extract host and port from rtsp://user:pass@host:port/path"""
    match = re.match(r"rtsp://(?:[^@]+@)?([^:/]+)(?::(\d+))?", rtsp_url or "")
    if not match:
        return None, None
    host = match.group(1)
    port = int(match.group(2)) if match.group(2) else 554
    return host, port


@router.get("/{camera_id}/ping", response_class=HTMLResponse)
async def ping_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """TCP reachability check for a camera's RTSP host:port. Returns HTML badge."""
    repo = CameraRepository(db)
    cameras = await repo.get_all()
    camera = next((c for c in cameras if c.id == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Skip ping for placeholder URLs
    if not camera.rtsp_url or camera.rtsp_url == "simulation_rtsp_url":
        return '<span class="px-2.5 py-0.5 text-[10px] font-medium rounded-full bg-zinc-50 text-zinc-500 border border-zinc-200">TANIMLANMADI</span>'

    host, port = _parse_rtsp_host_port(camera.rtsp_url)
    if not host:
        return '<span class="px-2.5 py-0.5 text-[10px] font-medium rounded-full bg-amber-50 text-amber-700 border border-amber-200">URL HATASI</span>'

    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=3.0
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return '<span class="px-2.5 py-0.5 text-[10px] font-medium rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block"></span>ONLİNE</span>'
    except Exception:
        return '<span class="px-2.5 py-0.5 text-[10px] font-medium rounded-full bg-red-50 text-red-700 border border-red-200">OFFLİNE</span>'
