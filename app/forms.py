from flask import request

def signup_form():
    return {
        "username": request.form.get("username"),
        "password": request.form.get("password")
    }

def login_form():
    return {
        "username": request.form.get("username"),
        "password": request.form.get("password")
    }