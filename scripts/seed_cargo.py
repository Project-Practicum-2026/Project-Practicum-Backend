import asyncio
import os
import sys
import random
import uuid
from datetime import datetime, UTC

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from app.cargo.models import Cargo
from app.warehouses.models import Warehouse
from sqlalchemy import select


# Типи вантажів для симуляції
CARGO_TYPES = [
    ("Електроніка", 50, 500, 0.5, 5),
    ("Меблі", 100, 800, 2, 15),
    ("Продукти харчування", 200, 2000, 1, 10),
    ("Будматеріали", 500, 5000, 3, 20),
    ("Одяг та текстиль", 50, 300, 1, 8),
    ("Автозапчастини", 100, 1000, 0.5, 6),
    ("Побутова хімія", 200, 1500, 1, 12),
    ("Медичне обладнання", 50, 400, 0.5, 4),
]

# Кількість вантажів на кожен склад відправлення
CARGO_PER_WAREHOUSE = 8


async def seed_cargo():
    async with AsyncSessionLocal() as db:
        warehouses_result = await db.execute(select(Warehouse))
        warehouses = warehouses_result.scalars().all()

        if not warehouses:
            print("No warehouses found. Run seed_warehouses.py first.")
            return

        # Очищаємо старі pending вантажі
        from sqlalchemy import delete
        await db.execute(
            delete(Cargo).where(Cargo.status == "pending")
        )
        await db.commit()

        added = 0
        warehouse_ids = [w.id for w in warehouses]

        for origin_warehouse in warehouses:
            # Для кожного складу генеруємо вантажі до інших складів
            other_warehouses = [w for w in warehouses if w.id != origin_warehouse.id]

            for i in range(CARGO_PER_WAREHOUSE):
                cargo_type, min_weight, max_weight, min_vol, max_vol = random.choice(CARGO_TYPES)
                dest_warehouse = random.choice(other_warehouses)

                cargo = Cargo(
                    external_id=f"EXT-{uuid.uuid4()}",
                    description=f"{cargo_type} зі складу {origin_warehouse.name} до {dest_warehouse.name}",
                    weight_kg=round(random.uniform(min_weight, max_weight), 2),
                    volume_m3=round(random.uniform(min_vol, max_vol), 2),
                    origin_warehouse_id=origin_warehouse.id,
                    dest_warehouse_id=dest_warehouse.id,
                    status="pending",
                    synced_at=datetime.now(UTC),
                )
                db.add(cargo)
                added += 1

        await db.commit()
        print(f"Added {added} cargo items across {len(warehouses)} warehouses.")
        print(f"Average per warehouse: {added // len(warehouses)}")


if __name__ == "__main__":
    asyncio.run(seed_cargo())