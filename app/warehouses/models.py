import uuid

from sqlalchemy import String, Numeric
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float] = mapped_column(Numeric(9, 6))
    contact_email: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(20))

    drivers: Mapped[list["Driver"]] = relationship(
        back_populates="home_warehouse"
    )
    origin_routes: Mapped[list["Route"]] = relationship(
        back_populates="origin_warehouse",
        foreign_keys="Route.origin_warehouse_id"
    )
    route_stops: Mapped[list["RouteStop"]] = relationship(
        back_populates="warehouse"
    )
    origin_cargo: Mapped[list["Cargo"]] = relationship(
        back_populates="origin_warehouse",
        foreign_keys="Cargo.origin_warehouse_id",
    )
    dest_cargo: Mapped[list["Cargo"]] = relationship(
        back_populates="dest_warehouse",
        foreign_keys="Cargo.dest_warehouse_id"
    )
    parked_vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="current_warehouse",
        foreign_keys="Vehicle.current_warehouse_id"
    )
