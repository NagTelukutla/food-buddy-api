from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

Base = declarative_base()
_engine = None
_SessionLocal = None


def _ensure_database_dir() -> None:
    settings = get_settings()
    db_dir = settings.database_path
    db_dir.mkdir(parents=True, exist_ok=True)


def get_engine():
    global _engine
    if _engine is None:
        _ensure_database_dir()
        settings = get_settings()
        db_url = settings.database_url
        if db_url.startswith("sqlite:///./"):
            rel = db_url.replace("sqlite:///", "")
            path = Path(rel)
            if not path.is_absolute():
                path = settings.base_dir / path
            db_url = f"sqlite:///{path.as_posix()}"
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(db_url, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def _migrate_order_status_column() -> None:
    """Normalize legacy order status values to the sequential workflow."""
    from sqlalchemy import inspect, text

    engine = get_engine()
    inspector = inspect(engine)
    if "orders" not in inspector.get_table_names():
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE orders SET status = 'Driver Assigned' "
                "WHERE status IN ('Preparing', 'Assigned to Driver')"
            )
        )
        conn.execute(
            text(
                "UPDATE orders SET status = 'Prepared' "
                "WHERE status IN ('Ready', 'Ready for Pickup')"
            )
        )
        conn.execute(
            text(
                "UPDATE orders SET status = 'Accepted' "
                "WHERE status = 'Awaiting Driver Acceptance'"
            )
        )


def _migrate_order_payment_columns() -> None:
    """Add payment columns to existing SQLite databases."""
    from sqlalchemy import inspect, text

    engine = get_engine()
    inspector = inspect(engine)
    if "orders" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("orders")}
    statements = []
    if "payment_status" not in columns:
        statements.append(
            "ALTER TABLE orders ADD COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid'"
        )
    if "razorpay_order_id" not in columns:
        statements.append("ALTER TABLE orders ADD COLUMN razorpay_order_id VARCHAR(64)")
    if statements:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))


def init_db() -> None:
    from app.models import audit_log, order  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
    _migrate_order_payment_columns()
    _migrate_order_status_column()


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
