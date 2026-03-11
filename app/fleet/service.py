import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.fleet.models import Vehicle
from app.fleet.schemas import VehicleStatus


async def get_all_vehicles(db: AsyncSession) -> list[Vehicle]:
    result = await db.execute(select(Vehicle).options(joinedload(Vehicle.vehicle_type)))
    return result.scalars().all()


async def get_vehicle_by_id(vehicle_id: uuid.UUID, db: AsyncSession) -> Vehicle | None:
    result = await db.execute(
        select(Vehicle)
        .options(joinedload(Vehicle.vehicle_type))
        .where(Vehicle.id == vehicle_id)
    )
    return result.scalar_one_or_none()


async def create_vehicle(
    plate_number: str,
    vehicle_type_id: uuid.UUID,
    db: AsyncSession
) -> Vehicle:
    vehicle = Vehicle(
        plate_number=plate_number,
        vehicle_type_id=vehicle_type_id,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def update_vehicle_status(vehicle: Vehicle, status: VehicleStatus, db: AsyncSession) -> Vehicle:
    vehicle.status = status
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def get_active_trips_with_last_gps(db: AsyncSession) -> list[dict]:
    from app.trips.models import Trip, GPSLog
    from sqlalchemy import func

    last_gps_log_sq = (
        select(
            GPSLog.trip_id,
            func.max(GPSLog.recorded_at).label("last_recorded_at")
        )
        .group_by(GPSLog.trip_id)
        .subquery()
    )

    query = (
        select(
            Trip.id.label("trip_id"),
            Vehicle.id.label("vehicle_id"),
            Vehicle.plate_number,
            GPSLog.latitude,
            GPSLog.longitude,
            GPSLog.recorded_at
        )
        .join(Vehicle, Trip.vehicle_id == Vehicle.id)
        .join(last_gps_log_sq, Trip.id == last_gps_log_sq.c.trip_id)
        .join(
            GPSLog,
            (GPSLog.trip_id == last_gps_log_sq.c.trip_id) &
            (GPSLog.recorded_at == last_gps_log_sq.c.last_recorded_at)
        )
        .where(Trip.status == "on_trip")
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    return [
        {
            "trip_id": row["trip_id"],
            "vehicle_id": row["vehicle_id"],
            "plate_number": row["plate_number"],
            "last_gps_position": {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "recorded_at": row["recorded_at"],
            } if row["latitude"] is not None else None,
        }
        for row in rows
    ]
