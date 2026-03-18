import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from sqlalchemy import delete, text


async def clear_db():
    async with AsyncSessionLocal() as db:
        print("🗑️  Починаємо очищення БД...")

        # Порядок важливий — спочатку дочірні таблиці, потім батьківські
        tables = [
            "gps_logs",
            "trip_crew",
            "trips",
            "route_stop_cargo",
            "route_stops",
            "routes",
            "cargo",
            "vehicles",
            "vehicle_types",
            "warehouses",
        ]

        for table in tables:
            await db.execute(text(f"DELETE FROM {table}"))
            print(f"  ✅ Очищено: {table}")

        await db.commit()
        print("\n🎉 БД повністю очищена!")


if __name__ == "__main__":
    asyncio.run(clear_db())