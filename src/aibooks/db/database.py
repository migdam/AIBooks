"""Database connection and session management."""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from loguru import logger

from .models import Base


# Enable foreign key support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Database:
    """Database manager for AIBooks."""

    def __init__(self, database_path: str | None = None):
        """Initialize database connection.

        Args:
            database_path: Path to SQLite database file. Defaults to ./aibooks.db
        """
        if database_path is None:
            database_path = os.getenv("DATABASE_PATH", "./aibooks.db")

        self.database_path = Path(database_path)
        self.database_url = f"sqlite:///{self.database_path}"

        # Create engine with connection pooling for SQLite
        self.engine = create_engine(
            self.database_url,
            echo=False,
            connect_args={"check_same_thread": False},  # Allow multi-threading
            pool_pre_ping=True,  # Verify connections before using
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        logger.info(f"Database initialized at: {self.database_path}")

    def create_tables(self):
        """Create all database tables."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all database tables. USE WITH CAUTION!"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope for database operations.

        Yields:
            SQLAlchemy Session object

        Example:
            with db.session_scope() as session:
                document = Document(title="Example")
                session.add(document)
                # Automatically commits on success, rolls back on error
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


# Global database instance
_db: Database | None = None


def get_db(database_path: str | None = None) -> Database:
    """Get or create the global database instance.

    Args:
        database_path: Path to SQLite database file

    Returns:
        Database instance
    """
    global _db
    if _db is None:
        _db = Database(database_path)
    return _db


def init_database(database_path: str | None = None, reset: bool = False):
    """Initialize the database and create tables.

    Args:
        database_path: Path to SQLite database file
        reset: If True, drop existing tables before creating new ones
    """
    db = get_db(database_path)

    if reset:
        db.drop_tables()

    db.create_tables()

    return db
