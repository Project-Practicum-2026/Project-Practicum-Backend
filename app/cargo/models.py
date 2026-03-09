import uuid
from datetime import datetime, UTC

from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core.database import Base


class Cargo(Base):
    __tablename__ = "cargo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(100), unique=True)
    destination: Mapped[str] = mapped_column(String(500))
    weight_kg: Mapped[float] = mapped_column(Numeric(10, 2))
    volume_m3: Mapped[float] = mapped_column(Numeric(10, 2))
    origin_warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id"))
    dest_warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    origin_warehouse: Mapped["Warehouse"] = relationship(
        back_populates="origin_cargo",
        foreign_keys=[origin_warehouse_id],
    )
    dest_warehouse: Mapped["Warehouse"] = relationship(
        back_populates="dest_cargo",
        foreign_keys=[dest_warehouse_id],
    )
    route_stop_cargo: Mapped[list["RouteStopCargo"]] = relationship(
        back_populates="cargo"
    )



