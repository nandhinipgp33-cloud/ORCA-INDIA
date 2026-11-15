import logging
from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseConfigurationError(RuntimeError):
    pass


class DatabaseNotConfiguredError(DatabaseConfigurationError):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not configured. Copy .env.example to .env and set it."
        )

    try:
        url = make_url(settings.database_url)
    except ArgumentError as error:
        raise DatabaseConfigurationError(
            "DATABASE_URL is not a valid SQLAlchemy database URL."
        ) from error

    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername != "postgresql+psycopg":
        raise DatabaseConfigurationError(
            "DATABASE_URL must use PostgreSQL with the psycopg 3 driver."
        )

    return create_engine(url, pool_pre_ping=True)


def get_db() -> Generator[Session, None, None]:
    session = Session(get_engine())
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        logger.exception("Database session failed")
        raise
    finally:
        session.close()


class Base(DeclarativeBase):
    pass
