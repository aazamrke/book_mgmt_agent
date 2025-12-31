from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# -------------------------------------------------
# Base class for all SQLAlchemy models
# -------------------------------------------------
Base = declarative_base()

# -------------------------------------------------
# Async SQLAlchemy Engine
# -------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# -------------------------------------------------
# Async Session Factory
# -------------------------------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# -------------------------------------------------
# Dependency for FastAPI routes
# -------------------------------------------------
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
