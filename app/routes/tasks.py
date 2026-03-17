import asyncio
import httpx
from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import get_celery_session
from app.core import base  # noqa: F401
from app.routes.models import Route, RouteStop, RouteStopCargo
from app.cargo.models import Cargo
from app.warehouses.models import Warehouse
from app.fleet.models import Vehicle


@shared_task(name="app.routes.tasks.build_routes")
def build_routes():
    async def _build_routes_async():

        # ── Крок 1: Читаємо всі дані ──────────────────────────────────────────
        async with get_celery_session() as db:
            # Отримуємо всі available ТЗ
            vehicles_result = await db.execute(
                select(Vehicle)
                .options(joinedload(Vehicle.vehicle_type))
                .where(
                    Vehicle.status == "available",
                    Vehicle.current_warehouse_id.is_not(None),
                )
            )
            vehicles = vehicles_result.unique().scalars().all()

            if not vehicles:
                print("No available vehicles found. Skipping route building.")
                return

            # Отримуємо pending вантажі
            pending_result = await db.execute(
                select(Cargo).where(Cargo.status == "pending")
            )
            pending_cargos = pending_result.scalars().all()

            if not pending_cargos:
                print("No pending cargo found. Skipping route building.")
                return

            # Отримуємо всі склади
            warehouses_result = await db.execute(select(Warehouse))
            all_warehouses = {w.id: w for w in warehouses_result.scalars().all()}

            # Збираємо available маршрути щоб скинути їх вантажі
            available_routes_result = await db.execute(
                select(Route)
                .options(
                    joinedload(Route.stops)
                    .joinedload(RouteStop.cargo_items)
                )
                .where(Route.status == "available")
            )
            available_routes = available_routes_result.unique().scalars().all()

            cargo_ids_from_routes = set()
            for route in available_routes:
                for stop in route.stops:
                    for item in stop.cargo_items:
                        cargo_ids_from_routes.add(item.cargo_id)

        # ── Крок 2: Видаляємо старі available маршрути ────────────────────────
        async with get_celery_session() as db:
            routes_result = await db.execute(
                select(Route.id).where(Route.status == "available")
            )
            route_ids = [r[0] for r in routes_result.all()]

            if route_ids:
                stops_result = await db.execute(
                    select(RouteStop.id).where(RouteStop.route_id.in_(route_ids))
                )
                stop_ids = [s[0] for s in stops_result.all()]

                if stop_ids:
                    await db.execute(
                        delete(RouteStopCargo).where(RouteStopCargo.route_stop_id.in_(stop_ids))
                    )
                await db.execute(
                    delete(RouteStop).where(RouteStop.route_id.in_(route_ids))
                )
                await db.execute(
                    delete(Route).where(Route.id.in_(route_ids))
                )
            await db.commit()

        # ── Крок 3: Скидаємо статус вантажів назад в pending ──────────────────
        async with get_celery_session() as db:
            if cargo_ids_from_routes:
                cargos_result = await db.execute(
                    select(Cargo).where(Cargo.id.in_(cargo_ids_from_routes))
                )
                for cargo in cargos_result.scalars().all():
                    cargo.status = "pending"
                await db.commit()

        # ── Крок 4: Формуємо запит до ORS Optimization ────────────────────────
        async with get_celery_session() as db:
            # Отримуємо актуальні pending вантажі
            pending_result = await db.execute(
                select(Cargo).where(Cargo.status == "pending")
            )
            pending_cargos = pending_result.scalars().all()

            if not pending_cargos:
                print("No pending cargo after reset. Skipping.")
                return

        # Формуємо shipments для ORS
        # Кожен вантаж = один shipment (pickup + delivery)
        shipments = []
        cargo_index_map = {}  # index → cargo для збереження результату

        for idx, cargo in enumerate(pending_cargos):
            origin = all_warehouses.get(cargo.origin_warehouse_id)
            dest = all_warehouses.get(cargo.dest_warehouse_id)

            if not origin or not dest:
                continue

            shipments.append({
                "amount": [
                    round(float(cargo.weight_kg)),
                    round(float(cargo.volume_m3) * 100),
                ],
                "pickup": {
                    "id": idx * 2,
                    "location": [float(origin.longitude),
                                 float(origin.latitude)],
                    "service": 1800,
                },
                "delivery": {
                    "id": idx * 2 + 1,
                    "location": [float(dest.longitude), float(dest.latitude)],
                    "service": 1800,
                },
            })
            cargo_index_map[idx] = cargo

        # Формуємо vehicles для ORS
        ors_vehicles = []
        vehicle_index_map = {}  # index → vehicle

        for idx, vehicle in enumerate(vehicles):
            warehouse = all_warehouses.get(vehicle.current_warehouse_id)
            if not warehouse:
                continue

            ors_vehicles.append({
                "id": idx,
                "profile": vehicle.vehicle_type.ors_profile,
                "start": [float(warehouse.longitude), float(warehouse.latitude)],
                "end": [float(warehouse.longitude), float(warehouse.latitude)],
                "capacity": [
                    round(float(vehicle.vehicle_type.max_weight_kg)),
                    round(float(vehicle.vehicle_type.max_volume_m3) * 100),
                ],
            })
            vehicle_index_map[idx] = vehicle

        if not shipments or not ors_vehicles:
            print("No shipments or vehicles to optimize.")
            return

        # ── Крок 5: Запит до ORS Optimization ────────────────────────────────
        async with httpx.AsyncClient() as client:
            try:
                print(
                    f"Sending {len(shipments)} shipments, {len(ors_vehicles)} vehicles")
                response = await client.post(
                    "https://api.openrouteservice.org/optimization",
                    headers={
                        "Authorization": settings.ORS_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "shipments": shipments,
                        "vehicles": ors_vehicles,
                        "options": {"g": True},
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                print(
                    f"ORS routes count: {len(result.get('routes', []))}")

            except httpx.HTTPError as e:
                print(f"ORS Optimization error: {e}")
                return

        # ── Крок 6: Зберігаємо маршрути в БД ──────────────────────────────────
        async with get_celery_session() as db:
            routes_built = 0

            for ors_route in result.get("routes", []):
                vehicle_idx = ors_route["vehicle"]
                vehicle = vehicle_index_map.get(vehicle_idx)

                if not vehicle:
                    continue

                steps = ors_route.get("steps", [])
                if not steps:
                    continue

                # Збираємо вантажі цього маршруту
                route_cargo_ids = set()
                for step in steps:
                    if step["type"] in ("pickup", "delivery"):
                        step_id = step["id"]
                        cargo_idx = step_id // 2
                        cargo = cargo_index_map.get(cargo_idx)
                        if cargo:
                            route_cargo_ids.add(cargo.id)

                if not route_cargo_ids:
                    continue

                # Розраховуємо загальні характеристики
                route_cargos_result = await db.execute(
                    select(Cargo).where(Cargo.id.in_(route_cargo_ids))
                )
                route_cargos = route_cargos_result.scalars().all()

                total_weight = sum(float(c.weight_kg) for c in route_cargos)
                total_volume = sum(float(c.volume_m3) for c in route_cargos)

                # FIX: ORS (VROOM) не має поля "summary" на рівні route.
                # Дистанція та тривалість зберігаються в кожному step.
                total_duration = sum(
                    step.get("duration", 0) for step in steps
                )
                total_distance = sum(step.get("distance", 0) for step in steps)
                if total_distance == 0:
                    total_distance = ors_route.get("distance", 0)

                # Знаходимо origin warehouse (перший pickup)
                origin_warehouse_id = vehicle.current_warehouse_id
                for step in steps:
                    if step["type"] == "pickup":
                        cargo_idx = step["id"] // 2
                        cargo = cargo_index_map.get(cargo_idx)
                        if cargo:
                            origin_warehouse_id = cargo.origin_warehouse_id
                            break

                # Створюємо маршрут
                route = Route(
                    status="available",
                    origin_warehouse_id=origin_warehouse_id,
                    total_distance_km=round(total_distance / 1000, 2),
                    estimated_duration_min=round(total_duration / 60),
                    total_weight_kg=round(total_weight, 2),
                    total_volume_m3=round(total_volume, 2),
                    version=0,
                )
                db.add(route)
                await db.flush()

                # Створюємо зупинки на основі кроків ORS
                stop_order = 0
                created_stops = {}  # (warehouse_id, action) → stop

                for step in steps:
                    if step["type"] not in ("pickup", "delivery"):
                        continue

                    cargo_idx = step["id"] // 2
                    cargo = cargo_index_map.get(cargo_idx)
                    if not cargo:
                        continue

                    if step["type"] == "pickup":
                        warehouse_id = cargo.origin_warehouse_id
                        action = "pickup"
                    else:
                        warehouse_id = cargo.dest_warehouse_id
                        action = "delivery"

                    # FIX: Відстань від попередньої зупинки з даних ORS step
                    step_distance_km = round(
                        step.get("distance", 0) / 1000, 2
                    )

                    # Якщо зупинка для цього складу вже є — додаємо вантаж
                    stop_key = (warehouse_id, action)
                    if stop_key not in created_stops:
                        stop = RouteStop(
                            route_id=route.id,
                            warehouse_id=warehouse_id,
                            stop_order=stop_order,
                            distance_from_prev_km=step_distance_km,
                        )
                        db.add(stop)
                        await db.flush()
                        created_stops[stop_key] = stop
                        stop_order += 1

                    db.add(RouteStopCargo(
                        route_stop_id=created_stops[stop_key].id,
                        cargo_id=cargo.id,
                        action=action,
                    ))

                # Оновлюємо статус вантажів
                for cargo in route_cargos:
                    cargo.status = "in_transit"

                routes_built += 1
                print(f"Built route for vehicle {vehicle.plate_number} "
                      f"with {len(route_cargos)} cargos, "
                      f"{round(total_distance / 1000, 2)} km")

            await db.commit()
            print(f"Total routes built: {routes_built}")

            # Вантажі які не потрапили в жоден маршрут
            unassigned = result.get("unassigned", [])
            if unassigned:
                print(f"Unassigned shipments: {len(unassigned)}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_build_routes_async())
    finally:
        loop.close()