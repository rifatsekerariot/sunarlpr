from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.core.database import get_db_session
from app.repositories.repositories import VehicleRepository
from app.api.schemas import VehicleCreate, VehicleUpdate, VehicleResponse
from app.models.models import Vehicle
from app.api.auth import get_current_user

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    query: str | None = None,
    status: str | None = None,
    vehicle_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    repo = VehicleRepository(db)
    return await repo.search_vehicles(query_str=query, status=status, vehicle_type=vehicle_type, skip=skip, limit=limit)

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    repo = VehicleRepository(db)
    vehicle = await repo.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_in: VehicleCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role not in ["ADMIN", "MANAGER", "OPERATOR"]:
        raise HTTPException(status_code=403, detail="Not authorized to register vehicles")
    repo = VehicleRepository(db)
    existing = await repo.get_by_plate(vehicle_in.plate_number)
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle plate already registered")
        
    vehicle = Vehicle(**vehicle_in.model_dump())
    new_vehicle = await repo.create(vehicle)
    await db.commit()
    return new_vehicle

@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_in: VehicleUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role not in ["ADMIN", "MANAGER", "OPERATOR"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit vehicles")
    repo = VehicleRepository(db)
    
    update_data = vehicle_in.model_dump(exclude_unset=True)
    vehicle = await repo.update(vehicle_id, **update_data)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    await db.commit()
    return vehicle

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete vehicles")
    repo = VehicleRepository(db)
    success = await repo.delete(vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    await db.commit()


from app.api.schemas import VehicleBulkDelete
@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_vehicles(
    payload: VehicleBulkDelete,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    if current_user.role not in ["ADMIN", "MANAGER"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete vehicles")
    
    from sqlalchemy import delete as sql_delete
    query = sql_delete(Vehicle).where(Vehicle.id.in_(payload.ids))
    await db.execute(query)
    await db.commit()

