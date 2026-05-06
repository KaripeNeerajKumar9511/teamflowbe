import os
from datetime import timedelta


class Config:
    # Secret key for signing JWTs and session cookies
    SECRET_KEY = os.environ.get("SECRET_KEY", "highly-secure-secret-key-for-team-task-manager-1234567890")

    # SQLite for easy local development. Swap this with your PostgreSQL URL in .env:
    # DATABASE_URL=postgresql://user:password@localhost:5432/taskmanager
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///taskmanager.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-long-jwt-secret-key-that-meets-security-requirements-32-chars")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_TOKEN_LOCATION = ["headers"]

    # Allow the frontend origin
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
