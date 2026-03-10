import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_access_token
from app.core.database import get_db
from app.auth.models import User



bearer_scheme = HTTPBearer()

DBSession = Annotated[AsyncSession, Depends(get_db)]
TokenCredentials = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]

async def get_current_user(credentials: TokenCredentials, db: DBSession) -> User:
    user_id = verify_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

async def require_manager(current_user: CurrentUser) -> User:
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: manager role required"
        )
    return current_user


async def require_driver(current_user: CurrentUser) -> User:
    if current_user.role != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: driver role required"
        )
    return current_user

ManagerUser = Annotated[User, Depends(require_manager)]
DriverUser = Annotated[User, Depends(require_driver)]