from fastapi import FastAPI
from app.core import base  # noqa: F401
from app.auth.router import router as auth_router
from app.drivers.router import router as drivers_route
from app.warehouses.router import router as warehouses_router

app = FastAPI(title="LogiGlobal API")

app.include_router(auth_router, prefix="/api/auth")
app.include_router(drivers_route, prefix="/api/drivers")
app.include_router(warehouses_router, prefix="/api")

