from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.settings import get_settings

settings = get_settings()

if settings.database_url:
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
else:
    engine = None
    async_session = None

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if not async_session:
        yield None
        return
    async with async_session() as session:
        yield session
