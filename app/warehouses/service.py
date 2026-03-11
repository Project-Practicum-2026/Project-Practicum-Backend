import math
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.warehouses.models import Warehouse


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r


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
