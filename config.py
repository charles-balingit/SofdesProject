class Config:
    SECRET_KEY = "secret-key-123"
    SQLALCHEMY_DATABASE_URI = os.environ.get("sqlite:///users.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
