from datetime import datetime, UTC, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, RefreshToken
from app.auth.schemas import TokenResponse
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def register_user(email: str, password: str, full_name: str, role: str,  db: AsyncSession) -> User:
    hashed_password = hash_password(password)
    user = User(
        email=email.lower(),
        password_hash=hashed_password,
        full_name=full_name,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    user = await get_user_by_email(email, db)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def create_tokens(user: User, db: AsyncSession) -> TokenResponse:
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(token)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role
    )


async def refresh_tokens(refresh_token: str, db: AsyncSession) -> TokenResponse | None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(UTC)
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        if verify_password(refresh_token, token.token_hash):
            token.revoked = True
            await db.commit()
            result = await db.execute(select(User).where(User.id == token.user_id))
            user = result.scalar_one_or_none()
            if not user:
                return None
            return await create_tokens(user, db)

    return None


async def revoke_refresh_token(refresh_token: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.revoked == False)
    )
    tokens = result.scalars().all()
    for token in tokens:
        if verify_password(refresh_token, token.token_hash):
            token.revoked = True
            await db.commit()
            break


