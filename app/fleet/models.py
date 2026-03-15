import uuid

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True)
    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicle_types.id"))
    status: Mapped[str] = mapped_column(String(20), default="available")
    current_warehouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("warehouses.id"), nullable=True)

    vehicle_type: Mapped["VehicleType"] = relationship(back_populates="vehicles")
    trips: Mapped[list["Trip"]] = relationship(back_populates="vehicle")
    current_warehouse: Mapped["Warehouse | None"] = relationship(foreign_keys=[current_warehouse_id])


class VehicleType(Base):
    __tablename__ = "vehicle_types"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    max_weight_kg: Mapped[float] = mapped_column(Numeric(10, 2))
    max_volume_m3: Mapped[float] = mapped_column(Numeric(10, 2))
    ors_profile: Mapped[str] = mapped_column(String(20), default="driving-hgv")

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="vehicle_type")