import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, ManagerUser
from app.core.database import get_db
from app.trips.schemas import (
    TripResponse,
    TripDetailResponse,
    TripCreate,
    TripStatusUpdate,
    TripStatus,
    ALLOWED_TRANSITIONS,
)
from app.trips.service import (
    get_all_trips,
    get_trip_by_id,
    create_trip,
    update_trip_status,
)

router = APIRouter(tags=["Trips"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[TripResponse])
async def list_trips(
    current_user: CurrentUser,
    db: DBSession,
):
    return await get_all_trips(
        db=db,
        current_user_id=current_user.id,
        role=current_user.role,
    )


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_new_trip(
    request: TripCreate,
    manager: ManagerUser,
    db: DBSession,
):
    trip = await create_trip(
        route_id=request.route_id,
        vehicle_id=request.vehicle_id,
        driver_ids=request.driver_ids,
        db=db,
    )
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create trip. Route must be taken and vehicle must be available.",
        )
    return trip


@router.get("/{trip_id}", response_model=TripDetailResponse)
async def get_trip(
    trip_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    trip = await get_trip_by_id(trip_id=trip_id, db=db)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )
    return trip


@router.post("/{trip_id}/status", response_model=TripResponse)
async def change_trip_status(
    trip_id: uuid.UUID,
    request: TripStatusUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    trip = await get_trip_by_id(trip_id=trip_id, db=db)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    current_status = TripStatus(trip.status)
    if request.status not in ALLOWED_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: {current_status} → {request.status}. "
                   f"Allowed: {[s.value for s in ALLOWED_TRANSITIONS[current_status]]}",
        )

    updated_trip = await update_trip_status(
        trip=trip,
        new_status=request.status,
        current_user_id=current_user.id,
        db=db,
    )
    if not updated_trip:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the primary driver of this trip can change its status.",
        )
    return updated_trip