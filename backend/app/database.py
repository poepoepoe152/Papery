"""Database engine, session, and initialization helpers."""
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries: int = 30, delay: float = 2.0) -> None:
    """Block until the database accepts connections (handles container startup)."""
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"[db] not ready (attempt {attempt}/{max_retries}): {exc}")
            time.sleep(delay)
    raise RuntimeError(f"Database not reachable: {last_err}")


def init_db() -> None:
    """Create tables. (Alembic migrations are introduced in a later phase.)"""
    from . import models  # noqa: F401  (ensure models are registered)

    wait_for_db()
    Base.metadata.create_all(bind=engine)
