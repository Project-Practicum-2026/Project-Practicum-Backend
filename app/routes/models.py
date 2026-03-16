import uuid
from datetime import datetime, UTC

from sqlalchemy import String, Numeric, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), default="available")
    origin_warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id"))
    total_distance_km: Mapped[float] = mapped_column(Numeric(10, 2))
    estimated_duration_min: Mapped[int] = mapped_column(Integer)
    crew_required: Mapped[bool] = mapped_column(Boolean(), default=False)
    version: Mapped[int] = mapped_column(Integer, default=0)
    total_weight_kg: Mapped[float] = mapped_column(Numeric(10, 2))
    total_volume_m3: Mapped[float] = mapped_column(Numeric(10, 2))
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


    trip: Mapped["Trip"] = relationship(back_populates="route")
    stops: Mapped[list["RouteStop"]] = relationship(back_populates="route")
    origin_warehouse: Mapped["Warehouse"] = relationship(
        back_populates="origin_routes",
        foreign_keys=[origin_warehouse_id]
    )


class RouteStop(Base):
    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routes.id"))
    warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id"))
    stop_order: Mapped[int] = mapped_column(Integer)
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    distance_from_prev_km: Mapped[float] = mapped_column(Numeric(10, 2))

    route: Mapped["Route"] = relationship(back_populates="stops")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="route_stops")
    cargo_items: Mapped[list["RouteStopCargo"]] = relationship(back_populates="route_stop")

class RouteStopCargo(Base):
    __tablename__ = "route_stop_cargo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    route_stop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("route_stops.id"))
    cargo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cargo.id"))
    action: Mapped[str] = mapped_column(String(20))

    route_stop: Mapped["RouteStop"] = relationship(back_populates="cargo_items")
    cargo: Mapped["Cargo"] = relationship(back_populates="route_stop_cargo")