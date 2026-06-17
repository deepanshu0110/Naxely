from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
import os
from typing import AsyncGenerator

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/databrief"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database dependency for FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()