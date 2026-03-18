import asyncio
import os
import sys
import uuid
from datetime import datetime, UTC, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from app.cargo.models import Cargo
from app.routes.models import Route, RouteStop, RouteStopCargo
from app.trips.models import Trip, TripCrew
from app.fleet.models import Vehicle
from app.drivers.models import Driver
from app.warehouses.models import Warehouse
from sqlalchemy import select


async def seed_trips():
    async with AsyncSessionLocal() as db:

        # ── 1. Перевіряємо наявність даних ───────────────────────────────────

        cargo_result = await db.execute(
            select(Cargo).where(Cargo.status == "pending")
        )
        cargos = cargo_result.scalars().all()

        if not cargos:
            print("❌ Немає pending вантажів. Спочатку запусти seed_cargo.py")
            return
        print(f"✅ Знайдено {len(cargos)} pending вантажів")

        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.status == "available")
        )
        vehicles = vehicle_result.scalars().all()

        if not vehicles:
            print("❌ Немає доступних ТЗ. Спочатку запусти seed_vehicles.py")
            return
        print(f"✅ Знайдено {len(vehicles)} доступних ТЗ")

        driver_result = await db.execute(select(Driver))
        drivers = driver_result.scalars().all()

        if not drivers:
            print("❌ Немає водіїв у БД")
            return
        print(f"✅ Знайдено {len(drivers)} водіїв")

        # ── 2. Групуємо вантажі по origin_warehouse_id ────────────────────────
        # Один маршрут = один склад відправлення
        groups: dict[uuid.UUID, list[Cargo]] = {}
        for cargo in cargos:
            groups.setdefault(cargo.origin_warehouse_id, []).append(cargo)

        print(f"✅ Буде створено {len(groups)} маршрутів (груп за складом відправлення)")

        # ── 3. Створюємо маршрути, рейси та екіпаж ───────────────────────────
        vehicle_idx = 0
        driver_idx = 0
        trips_created = 0

        for origin_warehouse_id, group_cargos in groups.items():

            if vehicle_idx >= len(vehicles):
                print("⚠️  Закінчились доступні ТЗ — зупиняємось")
                break
            if driver_idx >= len(drivers):
                print("⚠️  Закінчились водії — зупиняємось")
                break

            vehicle = vehicles[vehicle_idx]
            driver = drivers[driver_idx]

            total_weight = sum(float(c.weight_kg) for c in group_cargos)
            total_volume = sum(float(c.volume_m3) for c in group_cargos)

            # ── Route ─────────────────────────────────────────────────────────
            route = Route(
                status="taken",
                origin_warehouse_id=origin_warehouse_id,
                total_distance_km=0.0,
                estimated_duration_min=0,
                total_weight_kg=round(total_weight, 2),
                total_volume_m3=round(total_volume, 2),
                version=1,
            )
            db.add(route)
            await db.flush()

            # ── Зупинки: спочатку всі pickup, потім всі delivery ──────────────
            # Групуємо щоб не дублювати зупинки для одного складу
            stop_map: dict[tuple, dict] = {}

            for cargo in group_cargos:
                # Pickup
                pickup_key = (cargo.origin_warehouse_id, "pickup")
                if pickup_key not in stop_map:
                    stop_map[pickup_key] = {
                        "warehouse_id": cargo.origin_warehouse_id,
                        "action": "pickup",
                        "cargos": [],
                        "order": len(stop_map),
                    }
                stop_map[pickup_key]["cargos"].append(cargo)

            for cargo in group_cargos:
                # Delivery
                delivery_key = (cargo.dest_warehouse_id, "delivery")
                if delivery_key not in stop_map:
                    stop_map[delivery_key] = {
                        "warehouse_id": cargo.dest_warehouse_id,
                        "action": "delivery",
                        "cargos": [],
                        "order": len(stop_map),
                    }
                stop_map[delivery_key]["cargos"].append(cargo)

            # Сортуємо по порядку додавання
            stops_list = sorted(stop_map.values(), key=lambda x: x["order"])

            for stop_data in stops_list:
                estimated = datetime.now(UTC) + timedelta(hours=stop_data["order"] + 1)

                stop = RouteStop(
                    route_id=route.id,
                    warehouse_id=stop_data["warehouse_id"],
                    stop_order=stop_data["order"],
                    estimated_arrival=estimated,
                    actual_arrival=None,
                    distance_from_prev_km=0.0,
                )
                db.add(stop)
                await db.flush()

                for cargo in stop_data["cargos"]:
                    db.add(RouteStopCargo(
                        route_stop_id=stop.id,
                        cargo_id=cargo.id,
                        action=stop_data["action"],
                    ))

            # ── Trip ──────────────────────────────────────────────────────────
            trip = Trip(
                route_id=route.id,
                vehicle_id=vehicle.id,
                status="on_road",
                started_at=datetime.now(UTC),
            )
            db.add(trip)
            await db.flush()

            # ── TripCrew ──────────────────────────────────────────────────────
            db.add(TripCrew(
                trip_id=trip.id,
                driver_id=driver.id,
                role="primary",
            ))

            # ── Оновлюємо статуси ─────────────────────────────────────────────
            vehicle.status = "on_trip"
            for cargo in group_cargos:
                cargo.status = "in_transit"

            vehicle_idx += 1
            driver_idx += 1
            trips_created += 1

            print(
                f"  🚛 Trip #{trips_created}: "
                f"ТЗ={vehicle.plate_number} | "
                f"водій={driver.id} | "
                f"вантажів={len(group_cargos)} | "
                f"зупинок={len(stops_list)}"
            )

        await db.commit()
        print(f"\n🎉 Готово! Створено {trips_created} trips")


if __name__ == "__main__":
    asyncio.run(seed_trips())