import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.warehouses.models import Warehouse
from app.warehouses.schemas import Warehouse as WarehouseSchema


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


class WarehouseService:
    @staticmethod
    async def get_all_warehouses(db: AsyncSession) -> list[WarehouseSchema]:
        result = await db.execute(select(Warehouse))
        warehouses = result.scalars().all()
        return [WarehouseSchema.model_validate(w) for w in warehouses]

    @staticmethod
    async def get_nearest_warehouse(db: AsyncSession, lat: float, lng: float) -> WarehouseSchema | None:
        result = await db.execute(select(Warehouse))
        warehouses = result.scalars().all()

        if not warehouses:
            return None

        nearest = min(warehouses, key=lambda w: haversine(lat, lng, w.latitude, w.longitude))
        return WarehouseSchema.model_validate(nearest)