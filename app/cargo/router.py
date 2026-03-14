import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import ManagerUser
from app.cargo import service, schemas

router = APIRouter(tags=["Cargo"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[schemas.CargoResponse])
async def list_cargo(
    manager: ManagerUser,
    db: DBSession,
    status: schemas.CargoStatus | None = None
):
    """
    List all cargo. Managers only.
    """
    return await service.get_all_cargo(status=status, db=db)


@router.get("/{cargo_id}", response_model=schemas.CargoResponse)
async def get_cargo(cargo_id: uuid.UUID, db: DBSession):
    """
    Get details of a specific cargo.
    """
    db_cargo = await service.get_cargo_by_id(cargo_id=cargo_id, db=db)
    if db_cargo is None:
        raise HTTPException(status_code=404, detail="Cargo not found")
    return db_cargo
