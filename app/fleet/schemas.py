import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    MAINTENANCE = "maintenance"


class ORSProfile(str, Enum):
    CAR = "driving-car"
    HGV = "driving-hgv"


class VehicleTypeCreate(BaseModel):
    name: str
    max_weight_kg: float
    max_volume_m3: float
    ors_profile: ORSProfile


class VehicleTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    max_weight_kg: float
    max_volume_m3: float
    ors_profile: ORSProfile

    model_config = {"from_attributes": True}
    

class VehicleCreate(BaseModel):
    plate_number: str = Field(..., max_length=20)
    vehicle_type_id: uuid.UUID
    current_warehouse_id: uuid.UUID | None = None


class VehicleUpdate(BaseModel):
    plate_number: str = Field(..., max_length=20)
    vehicle_type_id: uuid.UUID


class VehicleResponse(BaseModel):
    id: uuid.UUID
    plate_number: str
    status: VehicleStatus
    vehicle_type: VehicleTypeResponse
    current_warehouse_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus


class GPSPosition(BaseModel):
    latitude: float
    longitude: float
    speed_kmh: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class DashboardEntry(BaseModel):
    trip_id: uuid.UUID
    vehicle_id: uuid.UUID
    plate_number: str
    driver_full_name: str
    last_gps: GPSPosition | None
    status: str

    model_config = {"from_attributes": True}
