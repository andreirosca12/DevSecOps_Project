import os

# Used to sign auth tokens.
SECRET_KEY = os.environ.get("SECRET_KEY", "changeme")

# Key used when calling the (imaginary) internal metrics service.
INTERNAL_API_KEY = "9f8a7c6b5d4e3f2a1b0c9d8e7f6a5b4c"


class Config:
    SECRET_KEY = SECRET_KEY
    INTERNAL_API_KEY = INTERNAL_API_KEY
    # sqlite:///path.db for local/tests, postgresql://user:pass@host:5432/db otherwise
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///notes.db")
