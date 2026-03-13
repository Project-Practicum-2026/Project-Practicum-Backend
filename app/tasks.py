import httpx
from celery import shared_task, chain
from app.core.database import get_db
from app.cargo import service as cargo_service
from app.cargo import schemas as cargo_schemas

@shared_task(name="app.tasks.sync_cargo_task")
def sync_cargo_task():
    """
    Fetches cargo data from an external API and upserts it into the database.
    """
    # This is a placeholder for the external API URL.
    EXTERNAL_API_URL = "https://example.com/api/cargo"
    
    try:
        with httpx.Client() as client:
            response = client.get(EXTERNAL_API_URL)
            response.raise_for_status()
            cargos_data = response.json()

            db = next(get_db())
            for cargo_data in cargos_data:
                cargo_create = cargo_schemas.CargoCreate(**cargo_data)
                cargo_service.upsert_cargo(db, cargo_create)
                
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (e.g., 404, 500)
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        # Handle network-related errors
        print(f"An error occurred while requesting {e.request.url!r}.")

    # After syncing, trigger the build_routes task
    chain(build_routes_task.s()).apply_async()


@shared_task(name="app.tasks.build_routes_task")
def build_routes_task():
    """
    Placeholder task for building routes.
    """
    print("Building routes...")
    # In a real scenario, this task would trigger the route building logic.
    return "Routes built successfully."
