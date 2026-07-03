"""
Database configuration and session management for Perfect Assistant.
Supports PostgreSQL (production) and SQLite (development).
"""

import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./perfect_assistant.db")

# URL-encode the password if it contains special characters
# This fixes connection strings with special characters like !!!
if "://" in DATABASE_URL and "@" in DATABASE_URL:
    parts = DATABASE_URL.split("://", 1)
    scheme = parts[0]
    rest = parts[1]
    
    if "@" in rest:
        # Extract user:password and host
        creds_and_host = rest.split("@", 1)
        creds = creds_and_host[0]
        host = creds_and_host[1]
        
        if ":" in creds:
            user, password = creds.split(":", 1)
            # URL-encode the password to handle special characters
            encoded_password = quote_plus(password)
            DATABASE_URL = f"{scheme}://{user}:{encoded_password}@{host}"

# Convert psycopg2 URL to asyncpg for async operations
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

# For SQLite, use aiosqlite
if DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite:///", 1)

print(f"Database URL: {DATABASE_URL}")

# Create async engine with SSL support for cloud databases
engine_kwargs = {
    "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true",
    "future": True,
    "pool_pre_ping": True,  # Verify connection before using
}

# Add SSL configuration for PostgreSQL connections
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    engine_kwargs["connect_args"] = {
        "ssl": "require",  # Force SSL for Supabase
        "command_timeout": 30,  # 30 second timeout
    }

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session in FastAPI."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()
