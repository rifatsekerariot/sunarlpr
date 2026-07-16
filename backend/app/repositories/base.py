from typing import Generic, TypeVar, Type, List, Any
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete
from app.models.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db_session: AsyncSession):
        self.model = model
        self.db_session = db_session

    async def get_by_id(self, id: UUID) -> T | None:
        result = await self.db_session.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        result = await self.db_session.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        self.db_session.add(entity)
        await self.db_session.flush()
        return entity

    async def update(self, id: UUID, **kwargs) -> T | None:
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def delete(self, id: UUID) -> bool:
        query = delete(self.model).where(self.model.id == id)
        result = await self.db_session.execute(query)
        return result.rowcount > 0
