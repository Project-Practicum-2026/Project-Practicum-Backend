import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.service import get_user_by_email
from app.auth.models import User
from app.core.security import hash_password
from app.drivers.models import Driver


async def get_all_drivers(db: AsyncSession) -> list[Driver]:
    result = await db.execute(select(Driver).options(joinedload(Driver.user)))
    return result.scalars().all()


async def get_driver_by_id(driver_id: uuid.UUID, db: AsyncSession) -> Driver | None:
    result = await db.execute(
        select(Driver)
        .options(joinedload(Driver.user))
        .where(Driver.id == driver_id)
    )
    return result.scalar_one_or_none()


async def get_driver_by_user_id(user_id: uuid.UUID, db: AsyncSession) -> Driver | None:
    result = await db.execute(
        select(Driver)
        .options(joinedload(Driver.user))
        .where(Driver.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_driver(
    email: str,
    password: str,
    full_name: str,
    phone: str | None,
    home_warehouse_id: uuid.UUID | None,
    db: AsyncSession
) -> Driver:
    existing = await get_user_by_email(email, db)
    if existing:
        return None

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        role="driver",
    )
    db.add(user)
    await db.flush()

    driver = Driver(
        user_id=user.id,
        home_warehouse_id=home_warehouse_id,
        status="unavailable",
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    await db.refresh(user)
    driver.user = user
    return driver


async def update_driver_status(driver: Driver, status: str, db: AsyncSession) -> Driver:
    driver.status = status
    await db.commit()
    await db.refresh(driver)
    return driver