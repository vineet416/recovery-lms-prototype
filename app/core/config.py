import os

# Settings come from environment variables (set by docker compose from .env).
DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
