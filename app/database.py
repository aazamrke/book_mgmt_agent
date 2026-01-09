from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event, text
from app.config import settings
from app.logging_config import get_logger
import asyncio
from typing import AsyncGenerator
import time

logger = get_logger(__name__)

# Production-grade engine configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    # Connection pool settings for production
    poolclass=NullPool,  # Use NullPool for async engines
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
    # Performance settings
    echo=settings.DEBUG,  # SQL logging only in debug mode
    future=True,
)

# Session factory with proper configuration
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Manual control over flushing
    autocommit=False
)

Base = declarative_base()

class DatabaseHealthCheck:
    """Database health monitoring"""
    
    def __init__(self):
        self.last_check = 0
        self.is_healthy = True
        self.check_interval = 30  # seconds
    
    async def check_health(self) -> bool:
        """Check database connectivity and performance"""
        current_time = time.time()
        
        # Skip if recently checked
        if current_time - self.last_check < self.check_interval:
            return self.is_healthy
        
        try:
            async with engine.begin() as conn:
                start_time = time.time()
                await conn.execute(text("SELECT 1"))
                query_time = time.time() - start_time
                
                # Log slow queries
                if query_time > 1.0:
                    logger.warning(f"Slow database health check: {query_time:.2f}s")
                
                self.is_healthy = True
                self.last_check = current_time
                
                logger.debug(f"Database health check passed: {query_time:.3f}s")
                return True
                
        except Exception as e:
            self.is_healthy = False
            logger.error(f"Database health check failed: {str(e)}")
            return False

# Global health checker
db_health = DatabaseHealthCheck()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Production-grade database session with proper error handling
    """
    session = AsyncSessionLocal()
    try:
        # Check database health periodically
        if not await db_health.check_health():
            logger.error("Database unhealthy, but proceeding with request")
        
        yield session
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        raise
    finally:
        await session.close()

async def init_database():
    """Initialize database with proper error handling"""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

async def close_database():
    """Cleanup database connections"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")

# Connection event listeners for monitoring
@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log new database connections"""
    logger.debug("New database connection established")

@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log connection checkout from pool"""
    logger.debug("Database connection checked out from pool")

@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log connection return to pool"""
    logger.debug("Database connection returned to pool")