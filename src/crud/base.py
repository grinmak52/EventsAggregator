from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orm import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDBase(Generic[ModelT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    async def get(self, session: AsyncSession, obj_id: int) -> ModelT | None:
        return await session.get(self.model, obj_id)

    async def get_all(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.id).offset(skip).limit(limit)
        result = await session.scalars(stmt)
        return list(result)

    async def create(self, session: AsyncSession, data: dict) -> ModelT:
        obj = self.model(**data)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession, obj: ModelT, data: dict) -> ModelT:
        for field, value in data.items():
            setattr(obj, field, value)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, obj: ModelT) -> None:
        await session.delete(obj)
        await session.commit()
