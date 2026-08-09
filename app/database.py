from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.logging import configure_logging
from settings.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.db_url, pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session_factory():

    return SessionLocal


async def create_database():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app):
    await create_database()
    configure_logging()
    yield

    await engine.dispose()
