from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import base  # noqa: F401
from app.auth.router import router as auth_router
from app.drivers.router import router as drivers_router
from app.warehouses.router import router as warehouses_router
from app.fleet.router import router as fleet_router
from app.cargo.router import router as cargo_router

app = FastAPI(title="LogiGlobal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(drivers_router, prefix="/api/drivers", tags=["drivers"])
app.include_router(warehouses_router, prefix="/api/warehouses", tags=["warehouses"])
app.include_router(fleet_router, prefix="/api/fleet", tags=["fleet"])
app.include_router(cargo_router, prefix="/api/cargo", tags=["cargo"])