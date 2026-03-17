import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from app.fleet.models import Vehicle, VehicleType
from app.warehouses.models import Warehouse
from sqlalchemy import select


# ТЗ які додаємо на кожен склад
# (vehicle_type_name, кількість)
VEHICLES_PER_WAREHOUSE = [
    ("Вантажівка", 2),
]


async def seed_vehicles():
    async with AsyncSessionLocal() as db:
        # Отримуємо всі склади
        warehouses_result = await db.execute(select(Warehouse))
        warehouses = warehouses_result.scalars().all()

        if not warehouses:
            print("No warehouses found. Run seed_warehouses.py first.")
            return

        # Отримуємо типи ТЗ
        types_result = await db.execute(select(VehicleType))
        vehicle_types = {vt.name: vt for vt in types_result.scalars().all()}

        if not vehicle_types:
            print("No vehicle types found. Create them via POST /api/fleet/vehicle-types first.")
            return

        added = 0
        plate_counter = 1

        for warehouse in warehouses:
            for type_name, count in VEHICLES_PER_WAREHOUSE:
                vt = vehicle_types.get(type_name)
                if not vt:
                    print(f"Vehicle type '{type_name}' not found, skipping.")
                    continue

                for _ in range(count):
                    plate = f"AA{plate_counter:04d}BB"
                    plate_counter += 1

                    # Перевіряємо чи не існує вже такий номер
                    existing = await db.execute(
                        select(Vehicle).where(Vehicle.plate_number == plate)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    vehicle = Vehicle(
                        plate_number=plate,
                        vehicle_type_id=vt.id,
                        status="available",
                        current_warehouse_id=warehouse.id,
                    )
                    db.add(vehicle)
                    added += 1

        await db.commit()
        print(f"Added {added} vehicles across {len(warehouses)} warehouses.")


if __name__ == "__main__":
    asyncio.run(seed_vehicles())