import asyncio

import httpx
from celery import shared_task
from sqlalchemy import select

from app.core import base  # noqa: F401
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.routes.models import Route, RouteStop
from app.warehouses.models import Warehouse


@shared_task(name="app.routes.tasks.build_routes")
def build_routes():
    async def _build_routes_async():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Route).where(Route.total_distance_km == 0)
            )
            routes = result.scalars().all()

            async with httpx.AsyncClient() as client:
                for route in routes:
                    stops_result = await db.execute(
                        select(RouteStop)
                        .where(RouteStop.route_id == route.id)
                        .order_by(RouteStop.stop_order)
                    )
                    stops = stops_result.scalars().all()

                    if len(stops) < 2:
                        continue

                    warehouse_ids = [s.warehouse_id for s in stops]
                    warehouses_result = await db.execute(
                        select(Warehouse).where(
                            Warehouse.id.in_(warehouse_ids))
                    )
                    warehouses = {w.id: w for w in
                                  warehouses_result.scalars().all()}

                    coordinates = [
                        [float(warehouses[s.warehouse_id].longitude),
                         float(warehouses[s.warehouse_id].latitude)]
                        for s in stops
                        if s.warehouse_id in warehouses
                    ]

                    if len(coordinates) < 2:
                        continue

                    try:
                        response = await client.post(
                            f"https://api.openrouteservice.org/v2/directions/driving-hgv",
                            headers={"Authorization": settings.ORS_API_KEY},
                            json={"coordinates": coordinates},
                            timeout=10.0,
                        )
                        response.raise_for_status()
                        data = response.json()

                        summary = data["routes"][0]["summary"]
                        total_distance_km = round(summary["distance"] / 1000,
                                                  2)
                        estimated_duration_min = round(
                            summary["duration"] / 60)

                        route.total_distance_km = total_distance_km
                        route.estimated_duration_min = estimated_duration_min

                    except httpx.HTTPError as e:
                        print(f"ORS error for route {route.id}: {e}")
                        continue

            await db.commit()
            print(f"Built {len(routes)} routes successfully")

    asyncio.run(_build_routes_async())
