import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.warehouses.models import Warehouse
from app.core.utils import haversine


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
