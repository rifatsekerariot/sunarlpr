from uuid import UUID
from typing import List
from sqlalchemy.future import select
from sqlalchemy import or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.models import Camera, Vehicle, AccessLog, User

class CameraRepository(BaseRepository[Camera]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Camera, db_session)

    async def get_active_cameras(self) -> List[Camera]:
        result = await self.db_session.execute(select(Camera).filter(Camera.is_active == True))
        return list(result.scalars().all())


class VehicleRepository(BaseRepository[Vehicle]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Vehicle, db_session)

    async def get_by_plate(self, plate_number: str) -> Vehicle | None:
        result = await self.db_session.execute(
            select(Vehicle).filter(Vehicle.plate_number == plate_number)
        )
        return result.scalars().first()

    async def search_vehicles(
        self,
        query_str: str | None = None,
        status: str | None = None,
        vehicle_type: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Vehicle]:
        stmt = select(Vehicle)
        
        filters = []
        if status:
            filters.append(Vehicle.status == status)
        if vehicle_type:
            filters.append(Vehicle.vehicle_type == vehicle_type)
        if query_str:
            search_pattern = f"%{query_str}%"
            filters.append(
                or_(
                    Vehicle.plate_number.ilike(search_pattern),
                    Vehicle.owner_name.ilike(search_pattern),
                    Vehicle.company.ilike(search_pattern),
                    Vehicle.department.ilike(search_pattern),
                    Vehicle.notes.ilike(search_pattern)
                )
            )

        if filters:
            stmt = stmt.filter(*filters)
            
        stmt = stmt.order_by(desc(Vehicle.created_at)).offset(skip).limit(limit)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())


class AccessLogRepository(BaseRepository[AccessLog]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(AccessLog, db_session)

    async def get_recent_logs(self, limit: int = 50) -> List[AccessLog]:
        stmt = select(AccessLog).order_by(desc(AccessLog.timestamp)).limit(limit)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def get_vehicle_history(self, plate_number: str, limit: int = 50) -> List[AccessLog]:
        stmt = (
            select(AccessLog)
            .filter(AccessLog.plate_number == plate_number)
            .order_by(desc(AccessLog.timestamp))
            .limit(limit)
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def search_logs(
        self,
        plate_number: str | None = None,
        camera_id: UUID | None = None,
        direction: str | None = None,
        is_authorized: bool | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AccessLog]:
        stmt = select(AccessLog)
        filters = []
        if plate_number:
            filters.append(AccessLog.plate_number.ilike(f"%{plate_number}%"))
        if camera_id:
            filters.append(AccessLog.camera_id == camera_id)
        if direction:
            filters.append(AccessLog.direction == direction)
        if is_authorized is not None:
            filters.append(AccessLog.is_authorized == is_authorized)
        if start_date:
            filters.append(AccessLog.timestamp >= start_date)
        if end_date:
            filters.append(AccessLog.timestamp <= end_date)

        if filters:
            stmt = stmt.filter(*filters)
            
        stmt = stmt.order_by(desc(AccessLog.timestamp)).offset(skip).limit(limit)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())


class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db_session.execute(
            select(User).filter(User.username == username)
        )
        return result.scalars().first()
