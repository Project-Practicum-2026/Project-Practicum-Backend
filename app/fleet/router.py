import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.routes.schemas import RouteDetailResponse
from app.routes.service import get_route_by_id
from app.trips.models import Trip
from app.auth.dependencies import ManagerUser
from app.core.database import get_db
from app.fleet.schemas import (
    VehicleResponse,
    VehicleTypeCreate,
    VehicleCreate,
    VehicleStatusUpdate,
    DashboardEntry,
    VehicleTypeResponse,
    VehicleUpdate,
    VehicleTypeUpdate,
    RouteStopEntry
)
from app.fleet.service import (
    get_all_vehicles,
    get_vehicle_by_id,
    create_vehicle_type,
    create_vehicle,
    update_vehicle_status,
    get_dashboard,
    get_all_vehicle_types,
    update_vehicle,
    delete_vehicle,
    update_vehicle_type,
    get_vehicle_type_by_id,
    delete_vehicle_type,
    get_trip_route
)

router = APIRouter(tags=["Fleet"])

DBSession = Annotated[AsyncSession, Depends(get_db)]



@router.get("/vehicle-types", response_model=list[VehicleTypeResponse])
async def list_vehicle_types(manager: ManagerUser, db: DBSession):
    return await get_all_vehicle_types(db)


@router.post("/vehicle-types", response_model=VehicleTypeResponse, status_code=status.HTTP_201_CREATED)
async def add_vehicle_type(request: VehicleTypeCreate, manager: ManagerUser, db: DBSession):
    return await create_vehicle_type(
        name=request.name,
        max_weight_kg=request.max_weight_kg,
        max_volume_m3=request.max_volume_m3,
        ors_profile=request.ors_profile,
        db=db,
    )


@router.get("/vehicles/", response_model=list[VehicleResponse])
async def list_vehicles(manager: ManagerUser, db: DBSession):
    return await get_all_vehicles(db)


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def add_vehicle(request: VehicleCreate, manager: ManagerUser, db: DBSession):
    return await create_vehicle(
        plate_number=request.plate_number,
        vehicle_type_id=request.vehicle_type_id,
        current_warehouse_id=request.current_warehouse_id,
        db=db,
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: uuid.UUID, manager: ManagerUser, db: DBSession):
    vehicle = await get_vehicle_by_id(vehicle_id, db)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    return vehicle


@router.patch("/vehicles/{vehicle_id}/status", response_model=VehicleResponse)
async def change_vehicle_status(
        vehicle_id: uuid.UUID,
        request: VehicleStatusUpdate,
        manager: ManagerUser,
        db: DBSession
):
    vehicle = await get_vehicle_by_id(vehicle_id, db)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    return await update_vehicle_status(vehicle, request.status, db=db)


@router.get("/dashboard/", response_model=list[DashboardEntry])
async def fleet_dashboard(manager: ManagerUser, db: DBSession):
    return await get_dashboard(db)


@router.get("/dashboard/{trip_id}/route", response_model=RouteDetailResponse)
async def dashboard_trip_route(trip_id: uuid.UUID, manager: ManagerUser, db: DBSession):
    result = await db.execute(select(Trip.route_id).where(Trip.id == trip_id))
    route_id = result.scalar_one_or_none()

    if not route_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    route = await get_route_by_id(route_id, db)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    return route

@router.patch("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def edit_vehicle(
    vehicle_id: uuid.UUID,
    request: VehicleUpdate,
    manager: ManagerUser,
    db: DBSession,
):
    vehicle = await get_vehicle_by_id(vehicle_id, db)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return await update_vehicle(
        vehicle,
        request.model_dump(exclude_unset=True),
        db,
    )


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vehicle(
    vehicle_id: uuid.UUID,
    manager: ManagerUser,
    db: DBSession,
):
    vehicle = await get_vehicle_by_id(vehicle_id, db)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    if not await delete_vehicle(vehicle, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete vehicle that is currently on a trip",
        )


@router.patch("/vehicle-types/{type_id}", response_model=VehicleTypeResponse)
async def edit_vehicle_type(
    type_id: uuid.UUID,
    request: VehicleTypeUpdate,
    manager: ManagerUser,
    db: DBSession,
):
    vtype = await get_vehicle_type_by_id(type_id, db)
    if not vtype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle type not found",
        )
    return await update_vehicle_type(
        vtype,
        request.model_dump(exclude_unset=True),
        db,
    )


@router.delete("/vehicle-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vehicle_type(
    type_id: uuid.UUID,
    manager: ManagerUser,
    db: DBSession,
):
    vtype = await get_vehicle_type_by_id(type_id, db)
    if not vtype:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle type not found",
        )
    if not await delete_vehicle_type(vtype, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete vehicle type — vehicles of this type exist",
        )