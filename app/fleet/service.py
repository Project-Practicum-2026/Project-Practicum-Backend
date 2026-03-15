import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.fleet.models import Vehicle, VehicleType
from app.fleet.schemas import VehicleStatus
from app.trips.models import Trip, TripCrew, GPSLog
from app.drivers.models import Driver
from app.auth.models import User


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


async def get_all_vehicle_types(db: AsyncSession) -> list[VehicleType]:
    result = await db.execute(select(VehicleType))
    return result.scalars().all()


async def create_vehicle_type(
    name: str,
    max_weight_kg: float,
    max_volume_m3: float,
    ors_profile: str,
    db: AsyncSession,
) -> VehicleType:
    vehicle_type = VehicleType(
        name=name,
        max_weight_kg=max_weight_kg,
        max_volume_m3=max_volume_m3,
        ors_profile=ors_profile,
    )
    db.add(vehicle_type)
    await db.commit()
    await db.refresh(vehicle_type)
    return vehicle_type


async def create_vehicle(
    plate_number: str,
    vehicle_type_id: uuid.UUID,
    current_warehouse_id: uuid.UUID | None,
    db: AsyncSession,
) -> Vehicle:
    vehicle = Vehicle(
        plate_number=plate_number,
        vehicle_type_id=vehicle_type_id,
        status=VehicleStatus.AVAILABLE,
        current_warehouse_id=current_warehouse_id,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)

    result = await db.execute(
        select(Vehicle)
        .options(joinedload(Vehicle.vehicle_type))
        .where(Vehicle.id == vehicle.id)
    )
    return result.scalar_one()


async def update_vehicle_status(vehicle: Vehicle, status: VehicleStatus, db: AsyncSession) -> Vehicle:
    vehicle.status = status
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def get_dashboard(db: AsyncSession) -> list[dict]:
    last_gps_sq = (
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
            Trip.status,
            Vehicle.id.label("vehicle_id"),
            Vehicle.plate_number,
            User.full_name.label("driver_full_name"),
            GPSLog.latitude,
            GPSLog.longitude,
            GPSLog.speed_kmh,
            GPSLog.recorded_at,
        )
        .join(Vehicle, Trip.vehicle_id == Vehicle.id)
        .join(TripCrew, (TripCrew.trip_id == Trip.id) & (TripCrew.role == "primary"))
        .join(Driver, TripCrew.driver_id == Driver.id)
        .join(User, Driver.user_id == User.id)
        .outerjoin(last_gps_sq, Trip.id == last_gps_sq.c.trip_id)
        .outerjoin(
            GPSLog,
            (GPSLog.trip_id == last_gps_sq.c.trip_id) &
            (GPSLog.recorded_at == last_gps_sq.c.last_recorded_at)
        )
        .where(Trip.status == "on_road") 
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    return [
        {
            "trip_id": row["trip_id"],
            "status": row["status"],
            "vehicle_id": row["vehicle_id"],
            "plate_number": row["plate_number"],
            "driver_full_name": row["driver_full_name"],
            "last_gps": {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "speed_kmh": row["speed_kmh"],
                "recorded_at": row["recorded_at"],
            } if row["latitude"] is not None else None,
        }
        for row in rows
    ]
