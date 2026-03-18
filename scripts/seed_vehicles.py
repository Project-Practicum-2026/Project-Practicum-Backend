import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from app.fleet.models import VehicleType, Vehicle
from app.warehouses.models import Warehouse
from sqlalchemy import select


VEHICLE_TYPES = [
    {
        "name": "Вантажівка",
        "max_weight_kg": 15000.0,
        "max_volume_m3": 50.0,
        "ors_profile": "driving-hgv",
    },
]

# ТЗ на кожен склад: (тип, кількість)
VEHICLES_PER_WAREHOUSE = [
    ("Вантажівка", 2),
]


async def seed_vehicles():
    async with AsyncSessionLocal() as db:

        # ── 1. Створюємо типи ТЗ якщо немає ─────────────────────────────────
        types_result = await db.execute(select(VehicleType))
        existing_types = {vt.name: vt for vt in types_result.scalars().all()}

        added_types = 0
        for vt_data in VEHICLE_TYPES:
            if vt_data["name"] not in existing_types:
                vt = VehicleType(**vt_data)
                db.add(vt)
                existing_types[vt_data["name"]] = vt
                added_types += 1

        await db.flush()
        print(f"✅ Типів ТЗ додано: {added_types} (існувало: {len(existing_types) - added_types})")

        # ── 2. Отримуємо склади ───────────────────────────────────────────────
        warehouses_result = await db.execute(select(Warehouse))
        warehouses = warehouses_result.scalars().all()

        if not warehouses:
            print("❌ Немає складів. Спочатку запусти seed_warehouses.py")
            return

        # ── 3. Створюємо ТЗ на кожен склад ───────────────────────────────────
        added_vehicles = 0
        plate_counter = 1

        # Беремо існуючий максимальний номер щоб не дублювати
        existing_vehicles_result = await db.execute(select(Vehicle))
        existing_plates = {v.plate_number for v in existing_vehicles_result.scalars().all()}

        for warehouse in warehouses:
            for type_name, count in VEHICLES_PER_WAREHOUSE:
                vt = existing_types.get(type_name)
                if not vt:
                    print(f"⚠️  Тип '{type_name}' не знайдено, пропускаємо")
                    continue

                for _ in range(count):
                    # Шукаємо вільний номер
                    while f"AA{plate_counter:04d}BB" in existing_plates:
                        plate_counter += 1

                    plate = f"AA{plate_counter:04d}BB"
                    existing_plates.add(plate)
                    plate_counter += 1

                    vehicle = Vehicle(
                        plate_number=plate,
                        vehicle_type_id=vt.id,
                        status="available",
                        current_warehouse_id=warehouse.id,
                    )
                    db.add(vehicle)
                    added_vehicles += 1
                    print(f"  🚛 {plate} → {warehouse.name}")

        await db.commit()
        print(f"\n✅ Додано {added_vehicles} ТЗ на {len(warehouses)} складів")


if __name__ == "__main__":
    asyncio.run(seed_vehicles())



