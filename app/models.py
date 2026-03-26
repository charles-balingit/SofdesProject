from . import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(200))
    lastname = db.Column(db.String(200))
    vehicle_type = db.Column(db.String(200))