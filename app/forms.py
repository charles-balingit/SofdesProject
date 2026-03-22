from flask import request

def signup_form():
    return {
        "firstname": request.form.get("firstname"),
        "lastname": request.form.get("lastname"),
        "email": request.form.get("email"),
        "vehicle_type": request.form.get("vehicle_type"),
        "username": request.form.get("username"),
        "password": request.form.get("password"),
        "confirm": request.form.get("confirm_password")
    }

def login_form():
    return {
        "username": request.form.get("username"),
        "password": request.form.get("password")
    }