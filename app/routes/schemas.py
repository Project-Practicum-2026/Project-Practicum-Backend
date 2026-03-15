import uuid
from enum import Enum

from datetime import datetime
from pydantic import BaseModel
from app.cargo.schemas import CargoResponse
from app.warehouses.schemas import WarehouseResponse


class RouteStatus(str, Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    CANCELLED = "cancelled"



class RouteStopCargoResponse(BaseModel):
    id: uuid.UUID
    cargo: CargoResponse
    action: str

    model_config = {"from_attributes": True}


class RouteStopResponse(BaseModel):
    id: uuid.UUID
    stop_order: int
    warehouse: WarehouseResponse
    estimated_arrival: datetime | None
    distance_from_prev_km: float
    cargo_items: list[RouteStopCargoResponse]

    model_config = {"from_attributes": True}


class RouteResponse(BaseModel):
    id: uuid.UUID
    status: RouteStatus
    version: int
    origin_warehouse_id: uuid.UUID
    total_distance_km: float
    estimated_duration_min: int
    total_weight_kg: float
    total_volume_m3: float
    built_at: datetime

    model_config = {"from_attributes": True}


class RouteDetailResponse(RouteResponse):
    stops: list[RouteStopResponse]
    origin_warehouse: WarehouseResponse

    model_config = {"from_attributes": True}

class TakeRouteRequest(BaseModel):
    version: int