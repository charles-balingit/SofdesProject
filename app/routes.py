from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.services.forecast_service import generate_forecast
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

    form_data = {}

    if request.method == "POST":

        data = signup_form()
        form_data = data

        username = data["username"]
        password = data["password"]

        email = request.form.get("email")
        confirm_password = request.form.get("confirm_password")

        # ✅ NEW FIELDS
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        vehicle_type = request.form.get("vehicle")

        # Password mismatch
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html", form_data=form_data)

        # Username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists.", "error")
            return render_template("signup.html", form_data=form_data)

        # ✅ Hash password
        hashed_pw = generate_password_hash(password)

        # ✅ CREATE USER (NOW SAVES ALL DATA)
        user = User(
            username=username,
            email=email,
            password=hashed_pw,
            firstname=firstname,
            lastname=lastname,
            vehicle_type=vehicle_type
        )

        db.session.add(user)
        db.session.commit()

        flash("✅ Account successfully created! You can now login.", "success")
        return redirect(url_for("main.signup"))

    return render_template("signup.html", form_data=form_data)

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
    return render_template("dashboard.html")


# ================= EV SMART ROUTING =================
@main.route("/ev-routing")
@login_required
def ev_routing():
    return render_template("ev_routing.html")


# ================= SALES FORECASTING =================
@main.route("/generate-forecast", methods=["POST"])
def generate_forecast_api():

    vehicle = request.json.get("vehicle")
    months = int(request.json.get("months"))

    data = generate_forecast(vehicle, months)

    return jsonify(data)

# ================= PARTS PROCUREMENT =================
@main.route("/parts-procurement")
@login_required
def parts_procurement():
    return render_template("parts_procurement.html")


# ================= PROFILE =================
@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)
