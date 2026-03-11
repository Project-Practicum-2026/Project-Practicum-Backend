import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    MAINTENANCE = "maintenance"


class VehicleBase(BaseModel):
    plate_number: str = Field(..., max_length=20)
    vehicle_type_id: uuid.UUID


class VehicleCreate(VehicleBase):
    pass


class VehicleResponse(VehicleBase):
    id: uuid.UUID
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus


class GPSPosition(BaseModel):
    latitude: float
    longitude: float
    recorded_at: datetime


class DashboardResponse(BaseModel):
    trip_id: uuid.UUID
    vehicle_id: uuid.UUID
    plate_number: str
    last_gps_position: GPSPosition | None
