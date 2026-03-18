import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.orm import joinedload

from app.auth.models import User
from app.drivers.models import Driver
from app.fleet.models import Vehicle, VehicleType
from app.fleet.schemas import VehicleStatus
from app.routes.models import Route, RouteStop
from app.trips.models import Trip, TripCrew, GPSLog
from app.warehouses.models import Warehouse


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

    first_order_sq = (
        select(
            RouteStop.route_id,
            func.min(RouteStop.stop_order).label("min_order")
        )
        .group_by(RouteStop.route_id)
        .subquery()
    )

    last_order_sq = (
        select(
            RouteStop.route_id,
            func.max(RouteStop.stop_order).label("max_order")
        )
        .group_by(RouteStop.route_id)
        .subquery()
    )

    FirstStop = aliased(RouteStop)
    LastStop = aliased(RouteStop)
    OriginWarehouse = aliased(Warehouse)
    DestWarehouse = aliased(Warehouse)

    query = (
        select(
            Trip.id.label("trip_id"),
            Trip.status,
            Trip.route_id,
            Vehicle.id.label("vehicle_id"),
            Vehicle.plate_number,
            User.full_name.label("driver_full_name"),
            OriginWarehouse.name.label("origin_name"),
            DestWarehouse.name.label("destination_name"),
            GPSLog.latitude,
            GPSLog.longitude,
            GPSLog.speed_kmh,
            GPSLog.recorded_at,
        )
        .join(Vehicle, Trip.vehicle_id == Vehicle.id)
        .join(Route, Trip.route_id == Route.id)
        .join(TripCrew, (TripCrew.trip_id == Trip.id) & (TripCrew.role == "primary"))
        .join(Driver, TripCrew.driver_id == Driver.id)
        .join(User, Driver.user_id == User.id)
        .join(first_order_sq, Route.id == first_order_sq.c.route_id)
        .join(FirstStop, (FirstStop.route_id == Route.id) & (FirstStop.stop_order == first_order_sq.c.min_order))
        .join(OriginWarehouse, FirstStop.warehouse_id == OriginWarehouse.id)
        .join(last_order_sq, Route.id == last_order_sq.c.route_id)
        .join(LastStop, (LastStop.route_id == Route.id) & (LastStop.stop_order == last_order_sq.c.max_order))
        .join(DestWarehouse, LastStop.warehouse_id == DestWarehouse.id)
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
            "route_id": row["route_id"],
            "status": row["status"],
            "vehicle_id": row["vehicle_id"],
            "plate_number": row["plate_number"],
            "driver_full_name": row["driver_full_name"],
            "origin": row["origin_name"],
            "destination": row["destination_name"],
            "last_gps": {
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "speed_kmh": float(row["speed_kmh"]) if row["speed_kmh"] else None,
                "recorded_at": row["recorded_at"],
            } if row["latitude"] is not None else None,
        }
        for row in rows
    ]


async def get_trip_route(trip_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    query = (
        select(
            RouteStop.id.label("stop_id"),
            RouteStop.stop_order,
            RouteStop.estimated_arrival,
            RouteStop.actual_arrival,
            RouteStop.distance_from_prev_km,
            Warehouse.name.label("warehouse_name"),
            Warehouse.address.label("warehouse_address"),
            Warehouse.latitude.label("warehouse_lat"),
            Warehouse.longitude.label("warehouse_lng"),
        )
        .join(Route, RouteStop.route_id == Route.id)
        .join(Trip, Trip.route_id == Route.id)
        .join(Warehouse, RouteStop.warehouse_id == Warehouse.id)
        .where(Trip.id == trip_id)
        .order_by(RouteStop.stop_order)
    )

    result = await db.execute(query)
    rows = result.mappings().all()

    return [
        {
            "stop_id": row["stop_id"],
            "stop_order": row["stop_order"],
            "warehouse_name": row["warehouse_name"],
            "warehouse_address": row["warehouse_address"],
            "latitude": float(row["warehouse_lat"]),
            "longitude": float(row["warehouse_lng"]),
            "estimated_arrival": row["estimated_arrival"],
            "actual_arrival": row["actual_arrival"],
            "distance_from_prev_km": float(row["distance_from_prev_km"]),
        }
        for row in rows
    ]

async def update_vehicle(
    vehicle: Vehicle,
    data: dict,
    db: AsyncSession,
) -> Vehicle:
    for field, value in data.items():
        setattr(vehicle, field, value)
    await db.commit()
    await db.refresh(vehicle)
    result = await db.execute(
        select(Vehicle)
        .options(joinedload(Vehicle.vehicle_type))
        .where(Vehicle.id == vehicle.id)
    )
    return result.scalar_one()


async def delete_vehicle(
    vehicle: Vehicle,
    db: AsyncSession,
) -> bool:
    if vehicle.status == VehicleStatus.ON_TRIP:
        return False
    await db.delete(vehicle)
    await db.commit()
    return True


async def update_vehicle_type(
    vehicle_type: VehicleType,
    data: dict,
    db: AsyncSession,
) -> VehicleType:
    for field, value in data.items():
        setattr(vehicle_type, field, value)
    await db.commit()
    await db.refresh(vehicle_type)
    return vehicle_type


async def get_vehicle_type_by_id(
    vehicle_type_id: uuid.UUID,
    db: AsyncSession,
) -> VehicleType | None:
    result = await db.execute(
        select(VehicleType).where(VehicleType.id == vehicle_type_id)
    )
    return result.scalar_one_or_none()


async def delete_vehicle_type(
    vehicle_type: VehicleType,
    db: AsyncSession,
) -> bool:
    result = await db.execute(
        select(Vehicle).where(Vehicle.vehicle_type_id == vehicle_type.id).limit(1)
    )
    if result.scalar_one_or_none():
        return False
    await db.delete(vehicle_type)
    await db.commit()
    return True