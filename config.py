import os

class Config:
    SECRET_KEY = "secret-key-123"
    SQLALCHEMY_DATABASE_URI = os.environ.get("https://allloykgdppuballvyan.supabase.co")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
