import random
import uuid
from datetime import datetime, UTC

from sqlalchemy import select

from app.core import base  # noqa: F401
from app.cargo.models import Cargo
from app.core.database import AsyncSessionLocal
from app.warehouses.models import Warehouse


async def seed_data():
    """
    This script simulates pulling data from an external database of warehouses
    and cargo and saving it to the project's database.
    """
    print("Seeding database with initial data as a fallback...")

    async with AsyncSessionLocal() as session:
        # For simplicity, let's check if warehouses exist before seeding.
        # In a real app, you might want a more robust check.
        result = await session.execute(select(Warehouse).limit(1))
        if result.first():
            print("Database already contains data. Skipping seed.")
            return

        # Create mock warehouses
        warehouse1 = Warehouse(
            name="Kyiv Central Warehouse",
            address="123 Khreshchatyk St, Kyiv, Ukraine",
            latitude=50.4501,
            longitude=30.5234,
            contact_email="kyiv.central@example.com",
            contact_phone="+380441234567",
        )
        warehouse2 = Warehouse(
            name="Lviv Regional Depot",
            address="456 Rynok Square, Lviv, Ukraine",
            latitude=49.8429,
            longitude=24.0311,
            contact_email="lviv.regional@example.com",
            contact_phone="+380322987654",
        )

        session.add_all([warehouse1, warehouse2])
        await session.commit()
        await session.refresh(warehouse1)
        await session.refresh(warehouse2)

        print(f"Created warehouse: {warehouse1.name} ({warehouse1.id})")
        print(f"Created warehouse: {warehouse2.name} ({warehouse2.id})")

        # Create mock cargo
        cargos_to_create = []
        for i in range(5):
            origin = warehouse1 if i % 2 == 0 else warehouse2
            destination = warehouse2 if i % 2 == 0 else warehouse1

            cargo = Cargo(
                external_id=f"EXT-{uuid.uuid4()}",
                description=f"Mock cargo {i+1} from {origin.name} to {destination.name}",
                weight_kg=random.uniform(10.5, 500.0),
                volume_m3=random.uniform(1.0, 15.0),
                origin_warehouse_id=origin.id,
                dest_warehouse_id=destination.id,
                status="pending",
                synced_at=datetime.now(UTC)
            )
            cargos_to_create.append(cargo)

        session.add_all(cargos_to_create)
        await session.commit()

        for cargo in cargos_to_create:
            await session.refresh(cargo)
            print(f"Created cargo: {cargo.id} (External: {cargo.external_id})")

        print("Database seeding complete.")
