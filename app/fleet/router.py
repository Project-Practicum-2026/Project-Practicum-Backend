import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import ManagerUser
from app.core.database import get_db
from app.fleet.schemas import (
    VehicleResponse,
    VehicleTypeCreate,
    VehicleCreate,
    VehicleStatusUpdate,
    DashboardEntry,
    VehicleTypeResponse
)
from app.fleet.service import (
    get_all_vehicles,
    get_vehicle_by_id,
    create_vehicle_type,
    create_vehicle,
    update_vehicle_status,
    get_dashboard,
    get_all_vehicle_types,
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
    vehicle = await create_vehicle(
        plate_number=request.plate_number,
        vehicle_type_id=request.vehicle_type_id,
        db=db
    )
    return vehicle


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
