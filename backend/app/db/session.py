from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url.get_secret_value(), pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session]:
    """Provide one synchronous request session with rollback and close guarantees.

    Workflow services own successful commit boundaries; this dependency handles only
    unhandled SQLAlchemy failures and resource cleanup.
    """
    session = get_session_factory()()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection(session: Session) -> None:
    """Execute the deliberately minimal database readiness probe."""
    session.execute(text("SELECT 1"))
