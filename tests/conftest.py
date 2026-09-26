"""
Pytest configuration.

Uses a single shared in-memory SQLite connection for all tests so tables
created by create_all() survive across sessions (each new connection to
sqlite:///:memory: gets a fresh empty database).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import backend.database as _db

# A single connection kept alive for the whole test session
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

# Reuse the same underlying connection so in-memory tables persist
@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    pass  # hook point; connection reuse is handled by StaticPool below


# Rebuild with StaticPool so every call to connect() returns the same connection
from sqlalchemy.pool import StaticPool  # noqa: E402

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

_db.engine = _test_engine
_db.SessionLocal = _TestSession

# Import app AFTER patching so main.py's create_all still works on our engine
# (main.py does `from backend.database import engine` which already captured the
# original engine reference — we therefore call create_all ourselves here)
import backend.models.complaint  # noqa: F401, E402 — registers Complaint with Base
from backend.database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

Base.metadata.create_all(bind=_test_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
