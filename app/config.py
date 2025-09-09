# core/config.py
import os
from datetime import timedelta

# ---------------------------
# App / Security Settings
# ---------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# JWT token expiration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# ---------------------------
# Cookie Settings
# ---------------------------
COOKIE_PARAMS = {
    "httponly": True,
    "samesite": "lax",
    "secure": False  # change to True in production with HTTPS
}

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

# ---------------------------
# Database Settings
# ---------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/yourdb")

# ---------------------------
# Misc / Defaults
# ---------------------------
# Default user roles
DEFAULT_USER_ROLE = "user"

# Optional: default session expiration
SESSION_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", 60))
