#!/usr/bin/env python3
"""
Network Coordinator Database Configuration

Fixed version with proper database session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./network_coordinator.db")

# FIXED: Proper SQLite configuration for thread safety
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        },
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=False  # Set to True for SQL debugging
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

# FIXED: Proper session configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # FIXED: Prevent issues with accessing objects after commit
)


def get_db() -> Session:
    """
    Database dependency for FastAPI
    FIXED: Proper session management with error handling
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    """Initialize database tables"""
    try:
        from .models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def test_database_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        # Simple test query
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the database connection
    test_database_connection()
    init_database()