from . import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))

    firstname = db.Column(db.String(150))
    lastname = db.Column(db.String(150))
    email = db.Column(db.String(150))
    vehicle_type = db.Column(db.String(150))
