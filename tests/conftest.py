"""
Shared pytest fixtures.

Points the app at a throwaway SQLite file for the whole test session —
the env var MUST be set before `config`/`app` are imported anywhere,
since `Config.SQLALCHEMY_DATABASE_URI` is computed once at import time.
"""
import os
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["SECRET_KEY"] = "test-secret-key-thats-plenty-long-enough"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-thats-plenty-long-enough"
os.environ["FLASK_DEBUG"] = "0"

import pytest  # noqa: E402  (import after env setup, see above)

from app import create_app, _init_database  # noqa: E402
from models import db as _db  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    os.close(_db_fd)
    try:
        os.unlink(_db_path)
    except OSError:
        pass


@pytest.fixture(scope="session")
def app():
    flask_app = create_app()
    flask_app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_tables(app):
    """Wipe all rows before every test, then reseed the default admin
    the same way the real app does — so tests don't leak state into
    each other but admin-only endpoints still have an admin to test against.
    """
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
    _init_database(app)
    yield
