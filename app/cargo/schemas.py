from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict


class CargoStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CargoBase(BaseModel):
    external_id: str
    description: str
    weight_kg: float
    volume_m3: float
    origin_warehouse_id: uuid.UUID
    dest_warehouse_id: uuid.UUID
    status: CargoStatus = CargoStatus.PENDING

    model_config = {"from_attributes": True}


class CargoCreate(CargoBase):
    pass


class CargoUpdate(CargoBase):
    pass


class CargoResponse(CargoBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

