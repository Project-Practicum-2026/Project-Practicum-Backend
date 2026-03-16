from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def get_celery_session():
    celery_engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=True,
        pool_size=1,
        max_overflow=0,
    )
    return async_sessionmaker(celery_engine, expire_on_commit=False)()