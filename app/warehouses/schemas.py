from pydantic import BaseModel, EmailStr
from uuid import UUID


class WarehouseBase(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    contact_email: EmailStr
    contact_phone: str | None = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(WarehouseBase):
    pass


class WarehouseResponse(WarehouseBase):
    id: UUID

    model_config = {"from_attributes": True}
