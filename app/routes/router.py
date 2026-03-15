import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import DriverUser, CurrentUser
from app.core.database import get_db
from app.routes.schemas import RouteResponse, RouteDetailResponse, \
    TakeRouteRequest
from app.routes.service import get_available_routes, get_route_by_id, \
    take_route

router = APIRouter(tags=["Routes"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/available", response_model=list[RouteResponse])
async def list_available_routes(
        warehouses_id: uuid.UUID,
        driver_id: DriverUser,
        db: DBSession
):
    return await get_available_routes(warehouses_id, db)


@router.get("/{route_id}", response_model=RouteDetailResponse)
async def get_route(
        route_id: uuid.UUID,
        driver_id: CurrentUser,
        db: DBSession
):
    route = await get_route_by_id(route_id, db)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return route

@router.post("/{route_id}/take", response_model=RouteResponse)
async def take_route_by_id(
        route_id: uuid.UUID,
        request: TakeRouteRequest,
        driver: DriverUser,
        db: DBSession
):
    route = await take_route(
        route_id=route_id,
        version=request.version,
        driver_id=driver.id,
        db=db
    )
    if not route:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Route is no longer available. Another driver may have taken it."
        )
    return route