import uuid
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.trips.models import Trip, TripCrew
from app.trips.schemas import TripStatus, ALLOWED_TRANSITIONS
from app.drivers.models import Driver
from app.routes.models import Route, RouteStop
from app.fleet.models import Vehicle


async def get_all_trips(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    role: str,
) -> list[Trip]:
    if role == "manager":
        result = await db.execute(
            select(Trip)
            .options(
                joinedload(Trip.vehicle),
                joinedload(Trip.route),
                selectinload(Trip.crew),
            )
        )
    else:
        driver_result = await db.execute(
            select(Driver).where(Driver.user_id == current_user_id)
        )
        driver = driver_result.scalar_one_or_none()
        if not driver:
            return []

        result = await db.execute(
            select(Trip)
            .join(TripCrew, TripCrew.trip_id == Trip.id)
            .where(TripCrew.driver_id == driver.id)
            .options(
                joinedload(Trip.vehicle),
                joinedload(Trip.route),
                selectinload(Trip.crew),
            )
        )

    return result.unique().scalars().all()


async def get_trip_by_id(
    trip_id: uuid.UUID,
    db: AsyncSession,
) -> Trip | None:
    result = await db.execute(
        select(Trip)
        .options(
            joinedload(Trip.vehicle).joinedload(Vehicle.vehicle_type),
            joinedload(Trip.route),
            selectinload(Trip.crew),
        )
        .where(Trip.id == trip_id)
    )
    return result.unique().scalar_one_or_none()


async def create_trip(
    route_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    driver_ids: list[uuid.UUID],
    db: AsyncSession,
) -> Trip | None:
    route_result = await db.execute(
        select(Route).where(Route.id == route_id)
    )
    route = route_result.scalar_one_or_none()
    if not route or route.status != "taken":
        return None

    vehicle_result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle or vehicle.status != "available":
        return None

    trip = Trip(
        route_id=route_id,
        vehicle_id=vehicle_id,
        status=TripStatus.WAITING,
    )
    db.add(trip)
    await db.flush()

    for idx, driver_id in enumerate(driver_ids):
        role = "primary" if idx == 0 else "secondary"
        db.add(TripCrew(
            trip_id=trip.id,
            driver_id=driver_id,
            role=role,
        ))

    vehicle.status = "on_trip"

    await db.commit()
    await db.refresh(trip)
    return trip


async def update_trip_status(
    trip: Trip,
    new_status: TripStatus,
    current_user_id: uuid.UUID,
    db: AsyncSession,
) -> Trip | None:
    current_status = TripStatus(trip.status)

    if new_status not in ALLOWED_TRANSITIONS[current_status]:
        return None

    driver_result = await db.execute(
        select(Driver).where(Driver.user_id == current_user_id)
    )
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return None

    crew_result = await db.execute(
        select(TripCrew).where(
            TripCrew.trip_id == trip.id,
            TripCrew.driver_id == driver.id,
            TripCrew.role == "primary",
        )
    )
    if not crew_result.scalar_one_or_none():
        return None

    trip.status = new_status

    if new_status == TripStatus.ON_ROAD:
        trip.started_at = datetime.now(UTC)

    if new_status == TripStatus.FINISHED:
        trip.finished_at = datetime.now(UTC)
        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == trip.vehicle_id)
        )
        vehicle = vehicle_result.scalar_one_or_none()
        if vehicle:
            vehicle.status = "available"
            from app.routes.models import Route, RouteStop
            route_result = await db.execute(
                select(RouteStop)
                .where(RouteStop.route_id == trip.route_id)
                .order_by(RouteStop.stop_order.desc())
            )
            last_stop = route_result.scalars().first()
            if last_stop:
                vehicle.current_warehouse_id = last_stop.warehouse_id

    await db.commit()
    await db.refresh(trip)
    return trip


async def confirm_stop_arrival(
    trip_id: uuid.UUID,
    stop_id: uuid.UUID,
    current_user_id: uuid.UUID,
    db: AsyncSession,
) -> dict | None:
    trip = await get_trip_by_id(trip_id, db)
    if not trip or trip.status != TripStatus.ON_ROAD:
        return None

    driver_result = await db.execute(
        select(Driver).where(Driver.user_id == current_user_id)
    )
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return None

    crew_result = await db.execute(
        select(TripCrew).where(
            TripCrew.trip_id == trip_id,
            TripCrew.driver_id == driver.id,
            TripCrew.role == "primary",
        )
    )
    if not crew_result.scalar_one_or_none():
        return None

    stop_result = await db.execute(
        select(RouteStop).where(RouteStop.id == stop_id)
    )
    stop = stop_result.scalar_one_or_none()
    if not stop:
        return None

    stop.actual_arrival = datetime.now(UTC)
    await db.flush()

    next_stop_result = await db.execute(
        select(RouteStop)
        .where(
            RouteStop.route_id == stop.route_id,
            RouteStop.stop_order == stop.stop_order + 1,
        )
    )
    next_stop = next_stop_result.scalar_one_or_none()

    await db.commit()
    await db.refresh(stop)

    return {
        "current_stop": stop,
        "next_stop": next_stop,
    }

async def add_crew_member(
    trip_id: uuid.UUID,
    driver_id: uuid.UUID,
    role: str,
    db: AsyncSession,
) -> TripCrew | None:
    existing = await db.execute(
        select(TripCrew).where(
            TripCrew.trip_id == trip_id,
            TripCrew.driver_id == driver_id,
        )
    )
    if existing.scalar_one_or_none():
        return None

    crew = TripCrew(trip_id=trip_id, driver_id=driver_id, role=role)
    db.add(crew)
    await db.commit()
    await db.refresh(crew)
    return crew


async def remove_crew_member(
    trip_id: uuid.UUID,
    crew_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    result = await db.execute(
        select(TripCrew).where(
            TripCrew.id == crew_id,
            TripCrew.trip_id == trip_id,
        )
    )
    crew = result.scalar_one_or_none()
    if not crew:
        return False
    if crew.role == "primary":
        raise ValueError("Cannot remove primary driver")
    await db.delete(crew)
    await db.commit()
    return True


async def get_trip_crew(
    trip_id: uuid.UUID,
    db: AsyncSession,
) -> list[TripCrew]:
    result = await db.execute(
        select(TripCrew).where(TripCrew.trip_id == trip_id)
    )
    return result.scalars().all()