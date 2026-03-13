import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import ManagerUser
from app.cargo import service, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.CargoResponse])
def list_cargo(
    manager: ManagerUser,
    db: Session = Depends(get_db),
    status: schemas.CargoStatus | None = None,
):
    """
    List all cargo. Managers only.
    """
    return service.get_all_cargo(db, status=status)


@router.get("/{cargo_id}", response_model=schemas.CargoResponse)
def get_cargo(
    cargo_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Get details of a specific cargo.
    """
    db_cargo = service.get_cargo_by_id(db, cargo_id=cargo_id)
    if db_cargo is None:
        raise HTTPException(status_code=404, detail="Cargo not found")
    return db_cargo
