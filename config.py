import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "toyota_secret_key")

    # Use Supabase on Vercel, SQLite locally
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///users.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False