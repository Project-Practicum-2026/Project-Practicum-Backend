from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.warehouses.service import WarehouseService
from app.warehouses.schemas import Warehouse as WarehouseSchema
from app.auth.dependencies import get_current_user  # Assuming this exists for auth

router = APIRouter()


@router.get("/warehouses", response_model=list[WarehouseSchema])
async def get_warehouses(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)  # For role check, but since both roles allowed, just ensure authenticated
):
    return await WarehouseService.get_all_warehouses(db)


@router.get("/warehouses/nearest", response_model=WarehouseSchema)
async def get_nearest_warehouse(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    warehouse = await WarehouseService.get_nearest_warehouse(db, lat, lng)
    if not warehouse:
        raise HTTPException(status_code=404, detail="No warehouses found")
    return warehouse