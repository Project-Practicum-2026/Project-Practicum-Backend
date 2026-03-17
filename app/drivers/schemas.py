import uuid
from pydantic import BaseModel, EmailStr

class UserInfo(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None
    role: str

    model_config = {"from_attributes": True}


class DriverResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    home_warehouse_id: uuid.UUID | None
    user: UserInfo

    model_config = {"from_attributes": True}

class DriverCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    home_warehouse_id: uuid.UUID | None = None


class DriverUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    home_warehouse_id: uuid.UUID | None = None


class DriverStatusUpdate(BaseModel):
    status: str