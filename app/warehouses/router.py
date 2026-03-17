import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.warehouses.schemas import (
    WarehouseResponse,
    WarehouseCreate,
    WarehouseUpdate
)
from app.auth.dependencies import CurrentUser, ManagerUser 
from app.warehouses.service import (
    get_all_warehouses,
    get_warehouse_by_id,
    create_warehouse,
    update_warehouse,
    get_nearest_warehouse,
    delete_warehouse
)

router = APIRouter(tags=["Warehouses"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[WarehouseResponse])
async def list_warehouses(current_user: CurrentUser, db: DBSession):
    return await get_all_warehouses(db)


@router.post("/", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def add_warehouse(request: WarehouseCreate, manager: ManagerUser, db: DBSession):
    return await create_warehouse(
        name=request.name,
        address=request.address,
        latitude=request.latitude,
        longitude=request.longitude,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone,
        db=db,
    )

@router.get("/nearest", response_model=WarehouseResponse)
async def nearest_warehouse(
    lat: Annotated[float, Query(description="Latitude")],
    lng: Annotated[float, Query(description="Longitude")],
    current_user: CurrentUser,
    db: DBSession,
):
    warehouse = await get_nearest_warehouse(db, lat, lng)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No warehouses found",
        )
    return warehouse


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    warehouse = await get_warehouse_by_id(warehouse_id, db)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return warehouse


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
async def edit_warehouse(
    warehouse_id: uuid.UUID,
    request: WarehouseUpdate,
    manager: ManagerUser,
    db: DBSession,
):
    warehouse = await get_warehouse_by_id(warehouse_id, db)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    return await update_warehouse(
        warehouse,
        request.model_dump(exclude_unset=True),
        db,
    )


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_warehouse(warehouse_id: uuid.UUID, manager: ManagerUser, db: DBSession):
    warehouse = await get_warehouse_by_id(warehouse_id, db)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )
    await delete_warehouse(warehouse, db)