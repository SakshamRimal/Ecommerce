from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True, #detects dead connections and removes them from the pool
    echo=settings.debug, #log all SQL queries in debug mode
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, #prevents automatic expiration of objects after commit
    autoflush=False, #prevents automatic flushing of changes to the database before queries
)

async def get_db_session():
    """FastAPI dependency that provides a database session for each request."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        