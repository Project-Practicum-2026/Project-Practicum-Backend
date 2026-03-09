from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RegisterRequest
)
from app.auth.service import (
    authenticate_user,
    register_user,
    create_tokens,
    refresh_tokens,
    revoke_refresh_token,
    get_user_by_email
)
from app.core.database import get_db


router = APIRouter(tags=["Auth"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: DBSession):
    existing_user = await get_user_by_email(request.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    user = await register_user(
        request.email,
        request.password,
        request.full_name,
        request.role,
        db
    )
    return await create_tokens(user, db)

@router.post("/token", response_model=TokenResponse)
async def login(request: LoginRequest, db: DBSession):
    user = await authenticate_user(request.email, request.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    return await create_tokens(user, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: DBSession):
    tokens = await refresh_tokens(request.refresh_token, db)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token is invalid"
        )
    return tokens


@router.post("/logout")
async def logout(request: RefreshRequest, db: DBSession):
    await revoke_refresh_token(request.refresh_token, db)
    return {"detail": "Successfully logged out"}