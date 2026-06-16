"""
Application configuration.

Reads database + secret settings from environment variables (with
sensible defaults) so the same code runs locally, on a server, or in CI.

Copy `.env.example` to `.env` and edit, or export the variables in your
shell before running `python app.py`.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

# Load variables from a local `.env` file if present.
load_dotenv()


def _build_mysql_uri() -> str:
    """Build a SQLAlchemy MySQL URI from individual env variables.

    PyMySQL is a pure-Python driver, so no native build tools are needed
    — just `pip install PyMySQL`.
    """
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    host = os.environ.get("MYSQL_HOST", "localhost")
    port = os.environ.get("MYSQL_PORT", "3306")
    db = os.environ.get("MYSQL_DB", "mindspace")
    # The `charset=utf8mb4` part lets the DB store emoji avatars correctly.
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


class Config:
    # ---- Secrets ----------------------------------------------------------
    # In production, ALWAYS override these via environment variables.
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-please")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-change-me-too")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # ---- Database ---------------------------------------------------------
    # Priority order:
    #   1. Full `DATABASE_URL` (e.g. mysql+pymysql://user:pass@host/db)
    #   2. MYSQL_* individual variables → MySQL URI
    #   3. Fallback to SQLite (handy for first-time local testing only)
    #
    # Set `USE_SQLITE=1` to force the SQLite fallback explicitly.
    if os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    elif os.environ.get("USE_SQLITE") == "1":
        SQLALCHEMY_DATABASE_URI = "sqlite:///mindspace.db"
    else:
        SQLALCHEMY_DATABASE_URI = _build_mysql_uri()

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Recycle connections — MySQL drops idle connections after 8h by default,
    # this prevents "MySQL server has gone away" errors.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # ---- Socket.IO + CORS ------------------------------------------------
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")

    # ---- Default admin account (seeded on first run) ---------------------
    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
