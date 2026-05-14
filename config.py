"""
Application configuration.
Keeps secrets and settings centralized and easy to change.
"""
import os
from datetime import timedelta


class Config:
    # Secret keys — in production, load these from environment variables
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-please")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-change-me-too")

    # JWT token lifetime
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # SQLite database lives next to the app file — simple and portable
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///mindspace.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Socket.IO allows cross-origin for the local dev frontend
    CORS_ALLOWED_ORIGINS = "*"

    # Default admin credentials seeded on first run
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"
