from pydantic import BaseModel
from uuid import UUID


class WarehouseBase(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    contact_email: str
    contact_phone: str | None = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(WarehouseBase):
    pass


class Warehouse(WarehouseBase):
    id: UUID

    class Config:
        from_attributes = True