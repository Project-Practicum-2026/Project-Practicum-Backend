import asyncio
import httpx
from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, joinedload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from app.routes.models import Route, RouteStop, RouteStopCargo
from app.cargo.models import Cargo
from app.warehouses.models import Warehouse
from app.fleet.models import Vehicle


@shared_task(name="app.routes.tasks.build_routes")
def build_routes():
    async def _build_routes_async():

        # ── Крок 1: Читаємо всі дані ──────────────────────────────────────────
        async with AsyncSessionLocal() as db:
            # Отримуємо всі available ТЗ з їх типами та складом базування
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

            # Отримуємо available маршрути щоб зібрати їх вантажі
            available_routes_result = await db.execute(
                select(Route)
                .options(
                    selectinload(Route.stops)
                    .selectinload(RouteStop.cargo_items)
                )
                .where(Route.status == "available")
            )
            available_routes = available_routes_result.unique().scalars().all()

            # Збираємо cargo_id з available маршрутів
            cargo_ids_from_routes = set()
            for route in available_routes:
                for stop in route.stops:
                    for item in stop.cargo_items:
                        cargo_ids_from_routes.add(item.cargo_id)

        # ── Крок 2: Видаляємо старі available маршрути ────────────────────────
        async with AsyncSessionLocal() as db:
            # Спочатку знаходимо id маршрутів
            routes_result = await db.execute(
                select(Route.id).where(Route.status == "available")
            )
            route_ids = [r[0] for r in routes_result.all()]

            if route_ids:
                # Знаходимо id зупинок
                stops_result = await db.execute(
                    select(RouteStop.id).where(
                        RouteStop.route_id.in_(route_ids))
                )
                stop_ids = [s[0] for s in stops_result.all()]

                # Видаляємо route_stop_cargo
                if stop_ids:
                    await db.execute(
                        delete(RouteStopCargo).where(
                            RouteStopCargo.route_stop_id.in_(stop_ids))
                    )

                # Видаляємо route_stops
                await db.execute(
                    delete(RouteStop).where(RouteStop.route_id.in_(route_ids))
                )

                # Видаляємо routes
                await db.execute(
                    delete(Route).where(Route.id.in_(route_ids))
                )

            await db.commit()

        # ── Крок 3: Скидаємо статус вантажів назад в pending ──────────────────
        async with AsyncSessionLocal() as db:
            if cargo_ids_from_routes:
                cargos_result = await db.execute(
                    select(Cargo).where(Cargo.id.in_(cargo_ids_from_routes))
                )
                for cargo in cargos_result.scalars().all():
                    cargo.status = "pending"
                await db.commit()

        # ── Крок 4: Отримуємо всі pending вантажі та склади ───────────────────
        async with AsyncSessionLocal() as db:
            pending_result = await db.execute(
                select(Cargo).where(Cargo.status == "pending")
            )
            pending_cargos = pending_result.scalars().all()

            if not pending_cargos:
                print("No pending cargo found. Skipping route building.")
                return

            warehouses_result = await db.execute(select(Warehouse))
            all_warehouses = {w.id: w for w in warehouses_result.scalars().all()}

        # ── Крок 5: Будуємо маршрут для кожного ТЗ ────────────────────────────
        async with AsyncSessionLocal() as db:
            async with httpx.AsyncClient() as client:
                # Копія вантажів щоб відстежувати які вже розподілені
                remaining_cargos = list(pending_cargos)

                for vehicle in vehicles:
                    if not remaining_cargos:
                        break

                    max_weight = float(vehicle.vehicle_type.max_weight_kg)
                    max_volume = float(vehicle.vehicle_type.max_volume_m3)
                    origin_warehouse_id = vehicle.current_warehouse_id
                    origin = all_warehouses.get(origin_warehouse_id)

                    if not origin:
                        continue

                    # ── Алгоритм підбору вантажів ──────────────────────────────

                    # Групуємо вантажі по dest_warehouse_id
                    dest_groups: dict = {}
                    for cargo in remaining_cargos:
                        dest_id = cargo.dest_warehouse_id
                        if dest_id not in dest_groups:
                            dest_groups[dest_id] = []
                        dest_groups[dest_id].append(cargo)

                    selected_cargos = []
                    route_stops_plan = []  # [(warehouse_id, [cargo], action)]
                    current_weight = 0.0
                    current_volume = 0.0

                    # Пріоритет 1 — знайти групу яка максимально заповнює ТЗ
                    # до одного кінцевого складу без проміжних зупинок
                    best_direct_group = None
                    best_direct_score = 0.0

                    for dest_id, cargos in dest_groups.items():
                        group_weight = sum(float(c.weight_kg) for c in cargos)
                        group_volume = sum(float(c.volume_m3) for c in cargos)

                        if group_weight <= max_weight and group_volume <= max_volume:
                            # Score — наскільки заповнює ТЗ (%)
                            score = (group_weight / max_weight + group_volume / max_volume) / 2
                            if score > best_direct_score:
                                best_direct_score = score
                                best_direct_group = (dest_id, cargos)

                    if best_direct_group:
                        dest_id, cargos = best_direct_group
                        selected_cargos = list(cargos)
                        current_weight = sum(float(c.weight_kg) for c in selected_cargos)
                        current_volume = sum(float(c.volume_m3) for c in selected_cargos)

                        route_stops_plan = [
                            (origin_warehouse_id, selected_cargos, "pickup"),
                            (dest_id, selected_cargos, "delivery"),
                        ]

                        # Пріоритет 2 — якщо ТЗ не повний добавляємо вантажі
                        # з інших груп по дорозі до кінцевого складу
                        fill_threshold = 0.85  # заповнений на 85%
                        is_full = (
                            current_weight / max_weight >= fill_threshold or
                            current_volume / max_volume >= fill_threshold
                        )

                        if not is_full:
                            for other_dest_id, other_cargos in dest_groups.items():
                                if other_dest_id == dest_id:
                                    continue

                                for cargo in other_cargos:
                                    if cargo in selected_cargos:
                                        continue
                                    cargo_weight = float(cargo.weight_kg)
                                    cargo_volume = float(cargo.volume_m3)

                                    if (current_weight + cargo_weight <= max_weight and
                                            current_volume + cargo_volume <= max_volume):
                                        selected_cargos.append(cargo)
                                        current_weight += cargo_weight
                                        current_volume += cargo_volume

                                        # Додаємо pickup на origin та delivery на проміжний склад
                                        route_stops_plan.insert(
                                            1,
                                            (other_dest_id, [cargo], "delivery")
                                        )

                    else:
                        # Пріоритет 3 — немає групи яка влізе повністю
                        # беремо найважчі вантажі до одного складу поки не заповнимо
                        sorted_cargos = sorted(
                            remaining_cargos,
                            key=lambda c: float(c.weight_kg),
                            reverse=True
                        )
                        main_dest_id = None

                        for cargo in sorted_cargos:
                            cargo_weight = float(cargo.weight_kg)
                            cargo_volume = float(cargo.volume_m3)

                            if (current_weight + cargo_weight <= max_weight and
                                    current_volume + cargo_volume <= max_volume):

                                if main_dest_id is None:
                                    main_dest_id = cargo.dest_warehouse_id

                                if cargo.dest_warehouse_id == main_dest_id:
                                    selected_cargos.append(cargo)
                                    current_weight += cargo_weight
                                    current_volume += cargo_volume

                        if not selected_cargos or not main_dest_id:
                            continue

                        route_stops_plan = [
                            (origin_warehouse_id, selected_cargos, "pickup"),
                            (main_dest_id, selected_cargos, "delivery"),
                        ]

                    if not selected_cargos:
                        continue

                    # ── Розрахунок відстані через ORS ─────────────────────────
                    unique_stops = []
                    seen = set()
                    for warehouse_id, _, _ in route_stops_plan:
                        if warehouse_id not in seen:
                            seen.add(warehouse_id)
                            unique_stops.append(warehouse_id)

                    coordinates = []
                    for warehouse_id in unique_stops:
                        w = all_warehouses.get(warehouse_id)
                        if w:
                            coordinates.append([float(w.longitude), float(w.latitude)])

                    total_distance_km = 0.0
                    estimated_duration_min = 0

                    if len(coordinates) >= 2:
                        try:
                            response = await client.post(
                                "https://api.openrouteservice.org/v2/directions/driving-hgv",
                                headers={"Authorization": settings.ORS_API_KEY},
                                json={"coordinates": coordinates},
                                timeout=10.0,
                            )
                            response.raise_for_status()
                            data = response.json()
                            summary = data["routes"][0]["summary"]
                            total_distance_km = round(summary["distance"] / 1000, 2)
                            estimated_duration_min = round(summary["duration"] / 60)

                        except httpx.HTTPError as e:
                            print(f"ORS error for vehicle {vehicle.id}: {e}")

                    # ── Створюємо маршрут в БД ─────────────────────────────────
                    total_weight_kg = sum(float(c.weight_kg) for c in selected_cargos)
                    total_volume_m3 = sum(float(c.volume_m3) for c in selected_cargos)

                    route = Route(
                        status="available",
                        origin_warehouse_id=origin_warehouse_id,
                        total_distance_km=total_distance_km,
                        estimated_duration_min=estimated_duration_min,
                        total_weight_kg=total_weight_kg,
                        total_volume_m3=total_volume_m3,
                        version=0,
                    )
                    db.add(route)
                    await db.flush()

                    # Створюємо зупинки
                    for order, (warehouse_id, stop_cargos, action) in enumerate(route_stops_plan):
                        stop = RouteStop(
                            route_id=route.id,
                            warehouse_id=warehouse_id,
                            stop_order=order,
                            distance_from_prev_km=0.0,
                        )
                        db.add(stop)
                        await db.flush()

                        for cargo in stop_cargos:
                            db.add(RouteStopCargo(
                                route_stop_id=stop.id,
                                cargo_id=cargo.id,
                                action=action,
                            ))

                    # Оновлюємо статус вантажів
                    cargo_ids = [c.id for c in selected_cargos]
                    cargos_result = await db.execute(
                        select(Cargo).where(Cargo.id.in_(cargo_ids))
                    )
                    for cargo in cargos_result.scalars().all():
                        cargo.status = "in_transit"

                    # Видаляємо розподілені вантажі з remaining
                    remaining_cargos = [
                        c for c in remaining_cargos
                        if c not in selected_cargos
                    ]

                    print(f"Built route for vehicle {vehicle.plate_number} "
                          f"with {len(selected_cargos)} cargos, "
                          f"{len(route_stops_plan)} stops, "
                          f"{total_distance_km} km")

            await db.commit()
            print(f"Built {len(vehicles)} routes successfully")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_build_routes_async())
    finally:
        loop.close()