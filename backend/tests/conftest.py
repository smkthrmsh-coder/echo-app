import pytest

from app.main import _run_migrations


@pytest.fixture(scope="session", autouse=True)
def _apply_sqlite_migrations():
    """Tests share the dev SQLite DB; apply the same additive column migrations main.py runs on startup."""
    _run_migrations()
