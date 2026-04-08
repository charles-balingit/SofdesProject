from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db
from app.models import User
from app.data_loader import (
    load_sales_data,
    load_parts_forecast_data,
    load_parts_actions_data,
    get_vehicle_models,
    get_parts_list,
)


# -----------------------------
# Home / Landing
# -----------------------------
@app.route('/')
def home():
    return render_template('home.html')


# -----------------------------
# Authentication
# -----------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('signup'))

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash('Username or email already exists.', 'warning')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# -----------------------------
# Main App Pages
# -----------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/ev-routing')
@login_required
def ev_routing():
    return render_template('ev_routing.html')


@app.route('/sales-forecasting')
@login_required
def sales_forecasting():
    vehicle_models = get_vehicle_models()
    return render_template(
        'sales_forecasting.html',
        vehicle_models=vehicle_models
    )


@app.route('/parts-procurement')
@login_required
def parts_procurement():
    parts_list = get_parts_list()
    return render_template(
        'parts_procurement.html',
        parts_list=parts_list
    )


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


# -----------------------------
# Sales Forecast API
# -----------------------------
@app.route('/api/sales-forecast', methods=['POST'])
@login_required
def api_sales_forecast():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON payload received."}), 400

    vehicle_model = data.get("vehicle_model")
    horizon = data.get("horizon", 1)

    if not vehicle_model:
        return jsonify({"error": "vehicle_model is required"}), 400

    try:
        horizon = int(horizon)
    except (TypeError, ValueError):
        return jsonify({"error": "horizon must be a number"}), 400

    if horizon < 1 or horizon > 12:
        return jsonify({"error": "horizon must be between 1 and 12"}), 400

    df = load_sales_data()

    # filter by vehicle model
    filtered = df[df["vehicle_model"] == vehicle_model].copy()

    if filtered.empty:
        return jsonify({"error": f"No sales data found for vehicle model '{vehicle_model}'"}), 404

    # keep only forecast rows, not actual rows
    if "series_type" in filtered.columns:
        filtered = filtered[
            filtered["series_type"].astype(str).str.lower() != "actual"
        ].copy()

    if filtered.empty:
        return jsonify({"error": f"No forecast rows found for vehicle model '{vehicle_model}'"}), 404

    # sort correctly
    if "forecast_step" in filtered.columns:
        filtered = filtered.sort_values("forecast_step")
    elif "month" in filtered.columns:
        filtered = filtered.sort_values("month")

    filtered = filtered.head(horizon)

    labels = filtered["month"].dt.strftime("%b %Y").tolist()
    values = filtered["value"].tolist()

    return jsonify({
        "vehicle_model": vehicle_model,
        "horizon": horizon,
        "labels": labels,
        "values": values
    })


# -----------------------------
# Parts Forecast API
# -----------------------------
@app.route('/api/parts-forecast', methods=['POST'])
@login_required
def api_parts_forecast():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON payload received."}), 400

    part_id = data.get("part_id")
    horizon = data.get("horizon", 1)

    if not part_id:
        return jsonify({"error": "part_id is required"}), 400

    try:
        horizon = int(horizon)
    except (TypeError, ValueError):
        return jsonify({"error": "horizon must be a number"}), 400

    if horizon < 1 or horizon > 12:
        return jsonify({"error": "horizon must be between 1 and 12"}), 400

    forecast_df = load_parts_forecast_data()
    actions_df = load_parts_actions_data()

    # filter forecast rows
    filtered_forecast = forecast_df[forecast_df["part_id"].astype(str) == str(part_id)].copy()

    if filtered_forecast.empty:
        return jsonify({"error": f"No parts forecast data found for part_id '{part_id}'"}), 404

    if "forecast_step" in filtered_forecast.columns:
        filtered_forecast = filtered_forecast.sort_values("forecast_step")
    elif "forecast_date" in filtered_forecast.columns:
        filtered_forecast = filtered_forecast.sort_values("forecast_date")

    filtered_forecast = filtered_forecast.head(horizon)

    labels = filtered_forecast["forecast_date"].dt.strftime("%b %Y").tolist()
    values = filtered_forecast["forecast_demand"].tolist()

    # match recommendation row for same part + selected horizon
    filtered_actions = actions_df[
        (actions_df["part_id"].astype(str) == str(part_id))
    ].copy()

    summary = {}

    if not filtered_actions.empty:
        if "forecast_step" in filtered_actions.columns:
            action_row = filtered_actions[filtered_actions["forecast_step"] == horizon]
        else:
            action_row = filtered_actions

        if not action_row.empty:
            row = action_row.iloc[0]
            summary = {
                "part_name": row["part_name"] if "part_name" in row else "",
                "forecast_demand": row["forecast_demand"] if "forecast_demand" in row else None,
                "current_stock": row["current_stock"] if "current_stock" in row else None,
                "on_order_qty": row["on_order_qty"] if "on_order_qty" in row else None,
                "recommended_order_qty": row["recommended_order_qty"] if "recommended_order_qty" in row else None,
                "alert_level": row["alert_level"] if "alert_level" in row else "N/A",
                "recommendation": row["recommendation"] if "recommendation" in row else "No recommendation available.",
                "supplier_name": row["supplier_name"] if "supplier_name" in row else ""
            }
        else:
            first_row = filtered_forecast.iloc[0]
            summary = {
                "part_name": first_row["part_name"] if "part_name" in first_row else "",
                "forecast_demand": None,
                "current_stock": None,
                "on_order_qty": None,
                "recommended_order_qty": None,
                "alert_level": "N/A",
                "recommendation": "No recommendation found for this selected horizon.",
                "supplier_name": ""
            }
    else:
        first_row = filtered_forecast.iloc[0]
        summary = {
            "part_name": first_row["part_name"] if "part_name" in first_row else "",
            "forecast_demand": None,
            "current_stock": None,
            "on_order_qty": None,
            "recommended_order_qty": None,
            "alert_level": "N/A",
            "recommendation": "No recommendation data found for this part.",
            "supplier_name": ""
        }

    return jsonify({
        "part_id": part_id,
        "horizon": horizon,
        "labels": labels,
        "values": values,
        "summary": summary
    })
