import uuid
from datetime import datetime, UTC
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routes.id"), unique=True)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vehicles.id"))
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    second_email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    route: Mapped["Route"] = relationship(back_populates="trip")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="trips")
    crew: Mapped[list["TripCrew"]] = relationship(back_populates="trip")
    gps_logs: Mapped[list["GPSLog"]] = relationship(back_populates="trip")


class TripCrew(Base):
    __tablename__ = "trip_crew"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id"))
    driver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drivers.id"))
    role: Mapped[str] = mapped_column(String(20))

    trip: Mapped["Trip"] = relationship(back_populates="crew")
    driver: Mapped["Driver"] = relationship(back_populates="trip_crew")


class GPSLog(Base):
    __tablename__ = "gps_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trips.id"), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    speed_kmh: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    trip: Mapped["Trip"] = relationship(back_populates="gps_logs")