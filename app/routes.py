from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from .models import User
from . import db
from .forms import signup_form, login_form

main = Blueprint("main", __name__)


# ---------------- HOME ----------------
@main.route("/")
def home():
    return render_template("home.html", user=current_user)


# ---------------- SIGNUP ----------------
@main.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        data = signup_form()

        username = data["username"]
        password = data["password"]
        confirm_password = data["confirm_password"]

        # ✅ Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("main.signup"))

        # ✅ Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists.", "error")
            return redirect(url_for("main.signup"))

        # ✅ Create user
        hashed_pw = generate_password_hash(password)

        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash("✅ Account successfully created! You can now login.", "success")
        return redirect(url_for("main.signup"))

    return render_template("signup.html")

# ---------------- LOGIN ----------------
@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        data = login_form()

        username = data["username"]
        password = data["password"]

        user = User.query.filter_by(username=username).first()

        # ✅ Username not found
        if not user:
            flash("Username does not exist.", "error")
            return redirect(url_for("main.login"))

        # ✅ Wrong password
        if not check_password_hash(user.password, password):
            flash("Incorrect password.", "error")
            return redirect(url_for("main.login"))

        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


# ================= DASHBOARD =================
@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)