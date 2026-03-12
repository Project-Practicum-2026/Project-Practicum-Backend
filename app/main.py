from fastapi import FastAPI
from app.core import base  # noqa: F401
from app.core.lifespan import lifespan
from app.auth.router import router as auth_router
from app.drivers.router import router as drivers_router
from app.warehouses.router import router as warehouses_router
from app.fleet.router import router as fleet_router

app = FastAPI(title="LogiGlobal API", lifespan=lifespan)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(drivers_router, prefix="/api/drivers")
app.include_router(warehouses_router, prefix="/api/warehouses")
app.include_router(fleet_router, prefix="/api/fleet")