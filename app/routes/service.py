import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.routes.models import Route, RouteStop, RouteStopCargo


async def get_available_routes(warehouse_id: uuid.UUID, db: AsyncSession) -> list[Route]:
    result = await db.execute(
        select(Route).where(
            Route.status=="available",
            Route.origin_warehouse_id==warehouse_id
        )
    )
    return result.scalars().all()


async def get_route_by_id(route_id: uuid.UUID, db: AsyncSession) -> Route | None:
    result = await db.execute(
        select(Route)
        .options(
            joinedload(Route.origin_warehouse),
            selectinload(Route.stops).joinedload(RouteStop.warehouse),
            selectinload(Route.stops).selectinload(RouteStop.cargo_items).joinedload(RouteStopCargo.cargo)
        )
        .where(Route.id == route_id)
    )
    return result.unique().scalar_one_or_none()


async def take_route(
        route_id: uuid.UUID,
        version: int,
        driver_id: uuid.UUID,
        db: AsyncSession
) -> Route | None:

    result = await db.execute(
        update(Route)
        .where(
            Route.id == route_id,
            Route.status == "available",
            Route.version == version
        )
        .values(
            status="taken",
            version=version + 1,
        )
        .returning(Route)
    )
    updated = result.scalar_one_or_none()
    await db.commit()
    return updated