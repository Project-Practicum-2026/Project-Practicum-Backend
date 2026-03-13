from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict


class CargoStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CargoBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: str
    destination: str
    weight_kg: float
    volume_m3: float
    origin_warehouse_id: uuid.UUID
    dest_warehouse_id: uuid.UUID
    status: CargoStatus = CargoStatus.PENDING


class CargoCreate(CargoBase):
    pass


class CargoUpdate(CargoBase):
    pass


class CargoResponse(CargoBase):
    id: uuid.UUID

