import asyncio
import httpx
from celery import shared_task, chain

from app.core.database import get_celery_session
from app.cargo import service as cargo_service
from app.cargo import schemas as cargo_schemas
from app.core.config import settings


@shared_task(name="app.cargo.tasks.sync_cargo")
def sync_cargo():
    async def _sync_cargo_async():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.EXTERNAL_API_URL)
                response.raise_for_status()
                cargos_data = response.json()

            async with get_celery_session() as session:
                for cargo_data in cargos_data:
                    cargo_create = cargo_schemas.CargoCreate(**cargo_data)
                    await cargo_service.upsert_cargo(cargo_data=cargo_create, db=session)

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            print(f"Could not connect to external API: {e}. Skipping sync.")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_sync_cargo_async())
    finally:
        loop.close()


