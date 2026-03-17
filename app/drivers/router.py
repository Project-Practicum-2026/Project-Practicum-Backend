import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.auth.dependencies import ManagerUser
from app.core.database import get_db
from app.drivers.schemas import (
    DriverResponse,
    DriverCreate,
    DriverUpdate,
    DriverStatusUpdate
)
from app.drivers.service import (
    get_all_drivers,
    get_driver_by_id,
    create_driver,
    update_driver,
    update_driver_status,
    delete_driver
)
router = APIRouter(tags=["Drivers"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[DriverResponse])
async def list_drivers(manager: ManagerUser, db: DBSession):
    return await get_all_drivers(db)


@router.post("/", response_model=DriverResponse, status_code=HTTP_201_CREATED)
async def add_driver(request: DriverCreate, manager: ManagerUser, db: DBSession):
    driver = await create_driver(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        home_warehouse_id=request.home_warehouse_id,
        db=db
    )
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    return driver


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: uuid.UUID, manager: ManagerUser, db: DBSession):
    driver = await get_driver_by_id(driver_id, db)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    return driver


@router.patch("/{driver_id}/status", response_model=DriverResponse)
async def change_driver_status(
        driver_id: uuid.UUID,
        request: DriverStatusUpdate,
        manager: ManagerUser,
        db: DBSession
):
    driver = await get_driver_by_id(driver_id, db)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    return await update_driver_status(driver, request.status, db=db)


@router.patch("/{driver_id}", response_model=DriverResponse)
async def edit_driver(
    driver_id: uuid.UUID,
    request: DriverUpdate,
    manager: ManagerUser,
    db: DBSession,
):
    driver = await get_driver_by_id(driver_id, db)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )
    try:
        return await update_driver(
            driver,
            request.model_dump(exclude_unset=True),
            db,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_driver(driver_id: uuid.UUID, manager: ManagerUser, db: DBSession):
    driver = await get_driver_by_id(driver_id, db)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    await delete_driver(driver, db)