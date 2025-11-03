from __future__ import annotations

from typing import Generic, TypeVar
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

from .config import settings

T = TypeVar("T", bound=BaseModel)


class Params(BaseModel):
    limit: int = Field(settings.PAGINATION_PER_PAGE, gt=0)
    offset: int = Field(0, gt=-1)


class Page(GenericModel, Generic[T]):
    items: list[T]
    total: int


async def paginate(session: AsyncSession, query: Select, params: Params) -> dict:
    """Paginate SQLAlchemy query results"""
    offset = params.offset
    limit = params.limit
    
    # Get total count - wrap query in a subquery for counting
    from sqlalchemy import alias
    subquery = query.alias()
    count_query = select(func.count()).select_from(subquery)
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated items
    paginated_query = query.offset(offset).limit(limit)
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
    }
