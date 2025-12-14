"""
PostgreSQL database connection and session management for hybrid model.
MongoDB is used for content, PostgreSQL for users, auth, and transactional data.
"""
from typing import Optional

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all PostgreSQL models"""
    pass


# Lazy initialization - engine created on first access
_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Get or create async engine (lazy initialization)"""
    global _engine
    if _engine is None:
        if not settings.POSTGRES_URL:
            raise ValueError("POSTGRES_URL is not configured. Please set DATABASE_URL or POSTGRES_URL environment variable.")
        _engine = create_async_engine(
            settings.POSTGRES_URL,
            echo=False,  # Set to True for SQL query logging
            future=True,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get or create async session factory (lazy initialization)"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        engine = get_engine()
        _AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


# For backward compatibility - create engine on import if POSTGRES_URL is set
# This allows existing code to work, but won't fail if POSTGRES_URL is empty
try:
    if settings.POSTGRES_URL:
        engine = get_engine()
        AsyncSessionLocal = get_session_factory()
    else:
        # Create dummy objects that will raise error on use
        engine = None  # type: ignore
        AsyncSessionLocal = None  # type: ignore
except Exception:
    # If engine creation fails, set to None
    engine = None  # type: ignore
    AsyncSessionLocal = None  # type: ignore


async def get_db() -> AsyncSession:
    """
    Dependency for getting async database session.
    Use in FastAPI route dependencies.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    if _engine is not None:
        await _engine.dispose()

