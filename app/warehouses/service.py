import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.warehouses.models import Warehouse
from app.core.utils import haversine
from app.cargo.models import Cargo
from app.routes.models import RouteStopCargo, RouteStop, Route
from app.drivers.models import Driver
from app.fleet.models import Vehicle


async def get_all_warehouses(db: AsyncSession) -> list[Warehouse]:
    result = await db.execute(select(Warehouse))
    return result.scalars().all()

async def get_warehouse_by_id(warehouse_id: uuid.UUID, db: AsyncSession) -> Warehouse:
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    return result.scalar_one_or_none()

async def create_warehouse(
    name: str,
    address: str,
    latitude: float,
    longitude: float,
    contact_email: str,
    contact_phone: str | None,
    db: AsyncSession,
):
    warehouse = Warehouse(
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
        contact_email=contact_email,
        contact_phone=contact_phone
    )
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse

async def get_nearest_warehouse(db: AsyncSession, lat: float, lng: float) -> Warehouse | None:
    result = await db.execute(select(Warehouse))
    warehouses = result.scalars().all()

    if not warehouses:
        return None

    nearest = min(warehouses, key=lambda w: haversine(lat, lng, w.latitude, w.longitude))
    return nearest

async def update_warehouse(
    warehouse: Warehouse,
    data: dict,
    db: AsyncSession,
) -> Warehouse:
    for field, value in data.items():
        setattr(warehouse, field, value)

    await db.commit()
    await db.refresh(warehouse)
    return warehouse


async def delete_warehouse(warehouse: Warehouse, db: AsyncSession) -> None:
    await db.execute(
        update(Driver)
        .where(Driver.home_warehouse_id == warehouse.id)
        .values(home_warehouse_id=None)
    )
    await db.execute(
        update(Vehicle)
        .where(Vehicle.current_warehouse_id == warehouse.id)
        .values(current_warehouse_id=None)
    )
    cargo_result = await db.execute(
        select(Cargo).where(
            (Cargo.origin_warehouse_id == warehouse.id) |
            (Cargo.dest_warehouse_id == warehouse.id)
        )
    )
    cargo_ids = [c.id for c in cargo_result.scalars().all()]
    if cargo_ids:
        await db.execute(
            delete(RouteStopCargo).where(RouteStopCargo.cargo_id.in_(cargo_ids))
        )
    await db.execute(
        delete(Cargo).where(
            (Cargo.origin_warehouse_id == warehouse.id) |
            (Cargo.dest_warehouse_id == warehouse.id)
        )
    )
    stops_result = await db.execute(
        select(RouteStop).where(RouteStop.warehouse_id == warehouse.id)
    )
    stop_ids = [s.id for s in stops_result.scalars().all()]

    if stop_ids:
        await db.execute(
            delete(RouteStopCargo).where(RouteStopCargo.route_stop_id.in_(stop_ids))
        )
    await db.execute(
        delete(RouteStop).where(RouteStop.warehouse_id == warehouse.id)
    )
    await db.execute(
        delete(Route).where(Route.origin_warehouse_id == warehouse.id)
    )

    await db.delete(warehouse)
    await db.commit()

