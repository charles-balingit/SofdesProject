import os

class Config:
<<<<<<< HEAD
    SECRET_KEY = "secret-key-123"
    SQLALCHEMY_DATABASE_URI = "sqlite:///users.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
=======
    SECRET_KEY = "toyota_secret_key"

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
>>>>>>> 9e9d8f7 (connect database)
