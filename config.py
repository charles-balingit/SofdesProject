import os

class Config:
    SECRET_KEY = "toyota_secret_key"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/users.db"   # ✅ Vercel writable location
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
