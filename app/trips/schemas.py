import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from app.routes.schemas import RouteResponse
from app.fleet.schemas import VehicleResponse


class TripStatus(str, Enum):
    WAITING = "waiting"
    LOADING = "loading"
    ON_ROAD = "on_road"
    UNLOADING = "unloading"
    FINISHED = "finished"


ALLOWED_TRANSITIONS = {
    TripStatus.WAITING: [TripStatus.LOADING],
    TripStatus.LOADING: [TripStatus.ON_ROAD],
    TripStatus.ON_ROAD: [TripStatus.UNLOADING],
    TripStatus.UNLOADING: [TripStatus.FINISHED],
    TripStatus.FINISHED: [],
}


class DriverInfo(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class TripCrewAdd(BaseModel):
    driver_id: uuid.UUID
    role: str = "secondary"


class TripCrewResponse(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    role: str

    model_config = {"from_attributes": True}


class TripCreate(BaseModel):
    route_id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_ids: list[uuid.UUID]


class TripResponse(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    vehicle_id: uuid.UUID
    status: TripStatus
    started_at: datetime | None
    finished_at: datetime | None
    first_email_sent: bool
    second_email_sent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TripDetailResponse(TripResponse):
    route: RouteResponse
    vehicle: VehicleResponse
    crew: list[TripCrewResponse]

    model_config = {"from_attributes": True}


class TripStatusUpdate(BaseModel):
    status: TripStatus


class NextStopInfo(BaseModel):
    id: uuid.UUID
    stop_order: int
    warehouse_id: uuid.UUID

class StopArrivalResponse(BaseModel):
    current_stop_id: uuid.UUID
    actual_arrival: datetime
    next_stop: NextStopInfo | None
    message: str