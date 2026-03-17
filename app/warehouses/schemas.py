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


class WarehouseUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None


class WarehouseResponse(WarehouseBase):
    id: UUID

    model_config = {"from_attributes": True}
