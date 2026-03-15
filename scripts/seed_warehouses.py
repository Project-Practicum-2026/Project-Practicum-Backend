import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.core import base  # noqa: F401
from app.warehouses.models import Warehouse


WAREHOUSES = [
    {
        "name": "Київ Центральний",
        "address": "вул. Хрещатик 1, Київ",
        "latitude": 50.4501,
        "longitude": 30.5234,
        "contact_email": "kyiv@logiglobal.com",
        "contact_phone": "+380441234567",
    },
    {
        "name": "Львів Регіональний",
        "address": "пл. Ринок 1, Львів",
        "latitude": 49.8429,
        "longitude": 24.0311,
        "contact_email": "lviv@logiglobal.com",
        "contact_phone": "+380322987654",
    },
    {
        "name": "Рівне Логістичний",
        "address": "вул. Соборна 1, Рівне",
        "latitude": 50.6199,
        "longitude": 26.2516,
        "contact_email": "rivne@logiglobal.com",
        "contact_phone": "+380362123456",
    },
    {
        "name": "Житомир Склад",
        "address": "вул. Велика Бердичівська 1, Житомир",
        "latitude": 50.2547,
        "longitude": 28.6587,
        "contact_email": "zhytomyr@logiglobal.com",
        "contact_phone": "+380412345678",
    },
    {
        "name": "Вінниця Дистрибуція",
        "address": "вул. Соборна 1, Вінниця",
        "latitude": 49.2331,
        "longitude": 28.4682,
        "contact_email": "vinnytsia@logiglobal.com",
        "contact_phone": "+380432567890",
    },
    {
        "name": "Хмельницький Термінал",
        "address": "вул. Проскурівська 1, Хмельницький",
        "latitude": 49.4229,
        "longitude": 26.9871,
        "contact_email": "khmelnytskyi@logiglobal.com",
        "contact_phone": "+380382678901",
    },
    {
        "name": "Луцьк Склад",
        "address": "вул. Лесі Українки 1, Луцьк",
        "latitude": 50.7472,
        "longitude": 25.3254,
        "contact_email": "lutsk@logiglobal.com",
        "contact_phone": "+380332789012",
    },
    {
        "name": "Тернопіль Логістика",
        "address": "вул. Руська 1, Тернопіль",
        "latitude": 49.5535,
        "longitude": 25.5948,
        "contact_email": "ternopil@logiglobal.com",
        "contact_phone": "+380352890123",
    },
]


async def seed_warehouses():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Warehouse))
        existing = result.scalars().all()
        existing_names = {w.name for w in existing}

        added = 0
        for data in WAREHOUSES:
            if data["name"] not in existing_names:
                db.add(Warehouse(**data))
                added += 1

        await db.commit()
        print(f"Added {added} warehouses. Total: {len(existing) + added}")


if __name__ == "__main__":
    asyncio.run(seed_warehouses())