from app.core.database import Base  # noqa: F401

from app.auth.models import User, RefreshToken  # noqa: F401
from app.drivers.models import Driver  # noqa: F401
from app.fleet.models import VehicleType, Vehicle  # noqa: F401
from app.warehouses.models import Warehouse  # noqa: F401
from app.cargo.models import Cargo  # noqa: F401
from app.routes.models import Route, RouteStop, RouteStopCargo  # noqa: F401
from app.trips.models import Trip, TripCrew, GPSLog  # noqa: F401