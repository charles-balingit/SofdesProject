from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .models import User
from .forms import signup_form, login_form
from .data_loader import (
    load_sales_data,
    load_parts_forecast_data,
    load_parts_actions_data,
    get_vehicle_models,
    get_parts_list,
)
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from io import StringIO

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('home.html')


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

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main.route('/ev-routing')
@login_required
def ev_routing():
    return render_template('ev_routing.html')


@main.route('/sales-forecasting')
@login_required
def sales_forecasting():
    vehicle_models = get_vehicle_models()
    return render_template(
        'sales_forecasting.html',
        vehicle_models=vehicle_models
    )


@main.route("/parts-procurement", methods=["GET", "POST"])
@login_required
def parts_procurement():
    parts = get_parts_list()
    selected_part = request.form.get("part_name") if request.method == "POST" else None

    chart_labels = []
    chart_datasets = []
    table_rows = []

    if selected_part:
        df = load_parts_forecast_data()

        if "part_name" in df.columns:
            part_df = df[df["part_name"].astype(str) == str(selected_part)].copy()
        else:
            part_df = df.iloc[0:0].copy()

        if not part_df.empty:
            if "forecast_date" in part_df.columns:
                part_df["forecast_date"] = part_df["forecast_date"].astype(str)

            if "model_key" in part_df.columns:
                model_keys = sorted(part_df["model_key"].dropna().astype(str).unique().tolist())
            else:
                model_keys = []

            if "forecast_step" in part_df.columns:
                part_df = part_df.sort_values(["forecast_step", "model_key"] if "model_key" in part_df.columns else ["forecast_step"])
            elif "forecast_date" in part_df.columns:
                part_df = part_df.sort_values(["forecast_date", "model_key"] if "model_key" in part_df.columns else ["forecast_date"])

            if "forecast_horizon_label" in part_df.columns:
                chart_labels = part_df["forecast_horizon_label"].dropna().astype(str).unique().tolist()
            elif "forecast_date" in part_df.columns:
                chart_labels = part_df["forecast_date"].dropna().astype(str).unique().tolist()

            for model in model_keys:
                model_df = part_df[part_df["model_key"].astype(str) == model].copy()

                if "forecast_step" in model_df.columns:
                    model_df = model_df.sort_values("forecast_step")
                elif "forecast_date" in model_df.columns:
                    model_df = model_df.sort_values("forecast_date")

                values = []
                for label in chart_labels:
                    row = model_df[model_df["forecast_horizon_label"].astype(str) == str(label)] if "forecast_horizon_label" in model_df.columns else model_df[model_df["forecast_date"].astype(str) == str(label)]
                    if not row.empty and "forecast_demand" in row.columns:
                        values.append(float(row.iloc[0]["forecast_demand"]))
                    else:
                        values.append(None)

                chart_datasets.append({
                   "label": model.replace("_", " ").title(),
                   "data": values
                })

            table_rows = part_df.to_dict(orient="records")

    return render_template(
        "parts_procurement.html",
        parts=parts,
        selected_part=selected_part,
        chart_labels=chart_labels,
        chart_datasets=chart_datasets,
        table_rows=table_rows,
    )

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@main.route('/api/sales-forecast', methods=['POST'])
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

    filtered = df[df["vehicle_model"] == vehicle_model].copy()

    if filtered.empty:
        return jsonify({"error": f"No sales data found for vehicle model '{vehicle_model}'"}), 404

    if "series_type" in filtered.columns:
        filtered = filtered[
            filtered["series_type"].astype(str).str.lower() != "actual"
        ].copy()

    if filtered.empty:
        return jsonify({"error": f"No forecast rows found for vehicle model '{vehicle_model}'"}), 404

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


@main.route('/api/parts-forecast', methods=['POST'])
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

    filtered_forecast = forecast_df[
        forecast_df["part_id"].astype(str) == str(part_id)
    ].copy()

    if filtered_forecast.empty:
        return jsonify({"error": f"No parts forecast data found for part_id '{part_id}'"}), 404

    if "forecast_step" in filtered_forecast.columns:
        filtered_forecast = filtered_forecast.sort_values("forecast_step")
    elif "forecast_date" in filtered_forecast.columns:
        filtered_forecast = filtered_forecast.sort_values("forecast_date")

    filtered_forecast = filtered_forecast.head(horizon)

    labels = filtered_forecast["forecast_date"].dt.strftime("%b %Y").tolist()
    values = filtered_forecast["forecast_demand"].tolist()

    filtered_actions = actions_df[
        actions_df["part_id"].astype(str) == str(part_id)
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

@main.route('/download_parts_csv/<part_name>')
@login_required
def download_parts_csv(part_name):
    df = load_parts_forecast_data()
    part_df = df[df['part_name'] == part_name]

    csv_data = part_df.to_csv(index=False)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={part_name}_forecast.csv"}
    )

@main.route('/api/parts-chart', methods=['POST'])
@login_required
def api_parts_chart():
    try:
        data = request.get_json()
        if not data or "part_name" not in data:
            return jsonify({"error": "Missing part_name"}), 400

        part_name = data.get("part_name")

        df = load_parts_forecast_data()

        if df is None or df.empty:
            return jsonify({"error": "Dataset empty"}), 500

        if "part_name" not in df.columns:
            return jsonify({"error": "Missing part_name column"}), 500

        part_df = df[df['part_name'] == part_name]

        if part_df.empty:
            return jsonify({"error": "No data found"}), 404

        # ✅ Ensure date column exists
        if "forecast_date" not in part_df.columns:
            return jsonify({"error": "Missing forecast_date column"}), 500

        # ✅ Convert to datetime (VERY IMPORTANT)
        part_df["forecast_date"] = pd.to_datetime(part_df["forecast_date"], errors='coerce')

        # ✅ Drop invalid dates
        part_df = part_df.dropna(subset=["forecast_date"])

        # ✅ Only sum numeric columns
        part_df = part_df.groupby("forecast_date", as_index=False).sum(numeric_only=True)

        labels = part_df["forecast_date"].dt.strftime("%b %Y").tolist()

        demand = part_df["forecast_demand"].tolist() if "forecast_demand" in part_df.columns else []
        supply = part_df["supply"].tolist() if "supply" in part_df.columns else []

        return jsonify({
            "labels": labels,
            "demand": demand,
            "supply": supply
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


@main.route("/parts-procurement/download", methods=["POST"])
@login_required
def download_parts_procurement_csv():
    selected_part = request.form.get("part_name")

    df = load_parts_forecast_data()

    if selected_part:
        df = df[df["part_name"].astype(str) == str(selected_part)].copy()

    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    safe_name = (selected_part or "all_parts").replace(" ", "_").lower()

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=parts_procurement_{safe_name}.csv"
        },
    )
