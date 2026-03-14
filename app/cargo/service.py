import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.cargo import models, schemas


async def get_cargo_by_id(cargo_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(models.Cargo).where(models.Cargo.id == cargo_id))
    return result.scalars().first()


async def get_all_cargo(status: schemas.CargoStatus | None, db: AsyncSession):
    query = select(models.Cargo)
    if status:
        query = query.where(models.Cargo.status == status)
    result = await db.execute(query)
    return result.scalars().all()


async def upsert_cargo(cargo_data: schemas.CargoCreate, db: AsyncSession):
    result = await db.execute(
        select(models.Cargo).where(models.Cargo.external_id == cargo_data.external_id)
    )
    db_cargo = result.scalars().first()

    if db_cargo:
        for key, value in cargo_data.model_dump().items():
            setattr(db_cargo, key, value)
    else:
        db_cargo = models.Cargo(**cargo_data.model_dump())
        db.add(db_cargo)

    await db.commit()
    await db.refresh(db_cargo)
    return db_cargo
