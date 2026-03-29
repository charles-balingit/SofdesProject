
# ============================================
# TOYOTA DSS - SALES FORECASTING FINAL MODEL
# Complete training and export script
# ============================================

import json
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple

from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =========================================================
# 1. CONFIG
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "SALES_FORCAST_DATASET.csv"
MODEL_DIR = BASE_DIR / "model"
DATA_DIR = BASE_DIR / "data"
TRAIN_END_DATE = "2025-01-01"
RANDOM_STATE = 42
FORECAST_HORIZONS = [1, 3]


# =========================================================
# 2. MODEL REGISTRY
# =========================================================
MODEL_CONFIGS = {
    "random_forest": {
        "model_name": "Random Forest",
        "estimator": RandomForestRegressor(
            n_estimators=400,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    },
    "extra_trees": {
        "model_name": "Extra Trees",
        "estimator": ExtraTreesRegressor(
            n_estimators=400,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    },
    "gradient_boosting": {
        "model_name": "Gradient Boosting",
        "estimator": GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=3,
            subsample=0.90,
            random_state=RANDOM_STATE
        )
    }
}


# =========================================================
# 3. HELPER DATACLASS
# =========================================================
@dataclass
class TrainedModelBundle:
    model_key: str
    model_name: str
    estimator: object
    feature_columns: List[str]
    static_info: pd.DataFrame
    monthly_defaults: pd.DataFrame
    history_by_vehicle: Dict[str, List[float]]
    last_date_by_vehicle: Dict[str, str]
    training_cutoff: str
    last_dataset_month: str


# =========================================================
# 4. LOAD + CLEAN DATA
# =========================================================
def load_and_prepare_dataset(dataset_path: Path) -> pd.DataFrame:
    df = pd.read_csv(dataset_path)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    df = df.drop(columns=["unnamed:_21"], errors="ignore")

    numeric_text_cols = [
        "industry_total_sales",
        "industry_passenger_sales",
        "industry_commercial_sales"
    ]
    for col in numeric_text_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

    df["date_month"] = pd.to_datetime(df["y"], format="%b-%Y")
    df = df.sort_values(["vehicle_model", "date_month"]).reset_index(drop=True)

    required_cols = [
        "units_sold",
        "vehicle_model",
        "vehicle_category",
        "powertrain_type",
        "promo_flag",
        "holiday_season_flag",
        "launch_flag",
        "price_band",
        "month",
        "quarter",
        "year",
        "lag_1",
        "lag_2",
        "lag_3",
        "rolling_mean_3",
        "rolling_mean_6",
        "trend_index",
        "industry_total_sales",
        "industry_passenger_sales",
        "industry_commercial_sales",
        "date_month"
    ]

    df = df.dropna(subset=required_cols).reset_index(drop=True)
    return df


# =========================================================
# 5. ENCODING + FEATURE BUILDING
# =========================================================
def build_encoded_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    categorical_cols = [
        "vehicle_model",
        "vehicle_category",
        "powertrain_type",
        "price_band"
    ]

    df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=False)
    drop_cols = ["units_sold", "y", "date_month"]
    feature_cols = [col for col in df_encoded.columns if col not in drop_cols]

    return df_encoded, feature_cols


# =========================================================
# 6. METRICS
# =========================================================
def calculate_metrics(y_true, y_pred) -> Dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse,
        "r2": float(r2_score(y_true, y_pred))
    }


# =========================================================
# 7. STATIC LOOKUPS FOR FUTURE FORECASTING
# =========================================================
def build_static_info(df: pd.DataFrame) -> pd.DataFrame:
    static_info = (
        df.sort_values(["vehicle_model", "date_month"])
          .groupby("vehicle_model", as_index=False)
          .tail(1)[["vehicle_model", "vehicle_category", "powertrain_type", "price_band"]]
          .reset_index(drop=True)
    )
    return static_info


def build_monthly_defaults(df: pd.DataFrame) -> pd.DataFrame:
    monthly_defaults = (
        df.groupby("month", as_index=False)
          .agg(
              promo_flag=("promo_flag", lambda s: int(round(s.mean()))),
              holiday_season_flag=("holiday_season_flag", lambda s: int(round(s.mean()))),
              launch_flag=("launch_flag", lambda s: int(round(s.mean()))),
              industry_total_sales=("industry_total_sales", "mean"),
              industry_passenger_sales=("industry_passenger_sales", "mean"),
              industry_commercial_sales=("industry_commercial_sales", "mean")
          )
    )

    monthly_defaults["launch_flag"] = 0
    return monthly_defaults


# =========================================================
# 8. BUILD FUTURE FEATURE ROW
# =========================================================
def build_future_row(
    vehicle_model: str,
    future_date: pd.Timestamp,
    history_values: List[float],
    static_lookup: pd.DataFrame,
    monthly_defaults: pd.DataFrame,
    feature_columns: List[str]
) -> pd.DataFrame:

    static_row = static_lookup.loc[static_lookup["vehicle_model"] == vehicle_model].iloc[0]
    month_num = int(future_date.month)
    quarter_num = int(((month_num - 1) // 3) + 1)
    defaults = monthly_defaults.loc[monthly_defaults["month"] == month_num].iloc[0]

    lag_1 = float(history_values[-1])
    lag_2 = float(history_values[-2]) if len(history_values) >= 2 else lag_1
    lag_3 = float(history_values[-3]) if len(history_values) >= 3 else lag_2
    rolling_mean_3 = float(np.mean(history_values[-3:]))
    rolling_mean_6 = float(np.mean(history_values[-6:]))

    row = {
        "vehicle_model": vehicle_model,
        "vehicle_category": static_row["vehicle_category"],
        "powertrain_type": static_row["powertrain_type"],
        "price_band": static_row["price_band"],
        "promo_flag": int(defaults["promo_flag"]),
        "holiday_season_flag": int(defaults["holiday_season_flag"]),
        "launch_flag": 0,
        "month": month_num,
        "quarter": quarter_num,
        "year": int(future_date.year),
        "lag_1": lag_1,
        "lag_2": lag_2,
        "lag_3": lag_3,
        "rolling_mean_3": rolling_mean_3,
        "rolling_mean_6": rolling_mean_6,
        "trend_index": len(history_values) + 1,
        "industry_total_sales": float(defaults["industry_total_sales"]),
        "industry_passenger_sales": float(defaults["industry_passenger_sales"]),
        "industry_commercial_sales": float(defaults["industry_commercial_sales"])
    }

    row_df = pd.DataFrame([row])

    row_df = pd.get_dummies(
        row_df,
        columns=["vehicle_model", "vehicle_category", "powertrain_type", "price_band"],
        drop_first=False
    )

    row_df = row_df.reindex(columns=feature_columns, fill_value=0)
    return row_df


# =========================================================
# 9. RECURSIVE FORECASTER
# =========================================================
def generate_recursive_forecast(bundle: TrainedModelBundle, horizon: int) -> pd.DataFrame:
    rows = []

    for vehicle_model, history_values in bundle.history_by_vehicle.items():
        working_history = list(history_values)
        last_date = pd.Timestamp(bundle.last_date_by_vehicle[vehicle_model])

        for step in range(1, horizon + 1):
            future_date = last_date + pd.offsets.MonthBegin(step)

            x_future = build_future_row(
                vehicle_model=vehicle_model,
                future_date=future_date,
                history_values=working_history,
                static_lookup=bundle.static_info,
                monthly_defaults=bundle.monthly_defaults,
                feature_columns=bundle.feature_columns
            )

            pred = float(bundle.estimator.predict(x_future)[0])
            pred = max(0.0, pred)
            working_history.append(pred)

            rows.append({
                "model_key": bundle.model_key,
                "model_name": bundle.model_name,
                "vehicle_model": vehicle_model,
                "forecast_horizon": horizon,
                "forecast_step": step,
                "forecast_month": future_date.strftime("%Y-%m-%d"),
                "predicted_units_sold": round(pred, 2)
            })

    return pd.DataFrame(rows)


# =========================================================
# 10. TRAIN + EXPORT EVERYTHING
# =========================================================
def train_and_export(df: pd.DataFrame) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df_encoded, feature_cols = build_encoded_features(df)

    x = df_encoded[feature_cols].copy()
    y = df_encoded["units_sold"].copy()

    train_mask = df_encoded["date_month"] < pd.Timestamp(TRAIN_END_DATE)
    test_mask = df_encoded["date_month"] >= pd.Timestamp(TRAIN_END_DATE)

    x_train = x.loc[train_mask].copy()
    x_test = x.loc[test_mask].copy()
    y_train = y.loc[train_mask].copy()
    y_test = y.loc[test_mask].copy()
    test_original = df.loc[test_mask].copy()

    static_info = build_static_info(df)
    monthly_defaults = build_monthly_defaults(df)

    history_by_vehicle = {
        vehicle: group["units_sold"].astype(float).tolist()
        for vehicle, group in df.groupby("vehicle_model")
    }

    last_date_by_vehicle = {
        vehicle: group["date_month"].max().strftime("%Y-%m-%d")
        for vehicle, group in df.groupby("vehicle_model")
    }

    metrics_rows = []
    prediction_frames = []
    forecast_frames = []
    model_registry = {}

    for model_key, config in MODEL_CONFIGS.items():
        model_name = config["model_name"]
        estimator = config["estimator"]

        print(f"Training: {model_name}")
        estimator.fit(x_train, y_train)

        y_pred = estimator.predict(x_test)
        y_pred = np.maximum(y_pred, 0)

        metrics = calculate_metrics(y_test, y_pred)
        metrics_rows.append({
            "model_key": model_key,
            "model_name": model_name,
            "mae": round(metrics["mae"], 4),
            "rmse": round(metrics["rmse"], 4),
            "r2": round(metrics["r2"], 4)
        })

        pred_df = test_original[["date_month", "vehicle_model", "units_sold"]].copy()
        pred_df["model_key"] = model_key
        pred_df["model_name"] = model_name
        pred_df["predicted_units_sold"] = np.round(y_pred, 2)
        pred_df["error"] = np.round(pred_df["units_sold"] - pred_df["predicted_units_sold"], 2)
        pred_df["abs_error"] = np.round(np.abs(pred_df["error"]), 2)
        prediction_frames.append(pred_df)

        bundle = TrainedModelBundle(
            model_key=model_key,
            model_name=model_name,
            estimator=estimator,
            feature_columns=feature_cols,
            static_info=static_info,
            monthly_defaults=monthly_defaults,
            history_by_vehicle=history_by_vehicle,
            last_date_by_vehicle=last_date_by_vehicle,
            training_cutoff=TRAIN_END_DATE,
            last_dataset_month=df["date_month"].max().strftime("%Y-%m-%d")
        )

        bundle_path = MODEL_DIR / f"{model_key}_bundle.pkl"
        joblib.dump(bundle, bundle_path)

        model_registry[model_key] = {
            "model_name": model_name,
            "bundle_path": str(bundle_path),
            "mae": round(metrics["mae"], 4),
            "rmse": round(metrics["rmse"], 4),
            "r2": round(metrics["r2"], 4)
        }

        if hasattr(estimator, "feature_importances_"):
            fi_df = pd.DataFrame({
                "feature": feature_cols,
                "importance": estimator.feature_importances_
            }).sort_values("importance", ascending=False)

            fi_df.to_csv(DATA_DIR / f"{model_key}_feature_importance.csv", index=False)

        for horizon in FORECAST_HORIZONS:
            forecast_df = generate_recursive_forecast(bundle, horizon)
            forecast_frames.append(forecast_df)

    metrics_df = pd.DataFrame(metrics_rows).sort_values("rmse").reset_index(drop=True)
    predictions_df = pd.concat(prediction_frames, ignore_index=True)
    forecasts_df = pd.concat(forecast_frames, ignore_index=True)

    history_df = df[["date_month", "vehicle_model", "units_sold"]].copy()
    history_df["month"] = history_df["date_month"].dt.strftime("%Y-%m-%d")
    history_df["value"] = history_df["units_sold"]
    history_df["series_type"] = "actual"
    history_df["model_key"] = "actual"
    history_df["model_name"] = "Actual Sales"
    history_df["forecast_horizon"] = 0
    history_df["forecast_step"] = 0

    history_graph_df = history_df[[
        "month", "vehicle_model", "value", "series_type",
        "model_key", "model_name", "forecast_horizon", "forecast_step"
    ]].copy()

    forecast_graph_df = forecasts_df.rename(columns={
        "forecast_month": "month",
        "predicted_units_sold": "value"
    }).copy()

    forecast_graph_df["series_type"] = "forecast"
    forecast_graph_df = forecast_graph_df[[
        "month", "vehicle_model", "value", "series_type",
        "model_key", "model_name", "forecast_horizon", "forecast_step"
    ]]

    graph_df = pd.concat([history_graph_df, forecast_graph_df], ignore_index=True)
    graph_df = graph_df.sort_values(
        ["vehicle_model", "model_key", "month", "forecast_horizon", "forecast_step"]
    ).reset_index(drop=True)

    metrics_df.to_csv(DATA_DIR / "model_metrics.csv", index=False)
    predictions_df.to_csv(DATA_DIR / "backtest_predictions.csv", index=False)
    forecasts_df.to_csv(DATA_DIR / "future_forecasts.csv", index=False)
    graph_df.to_csv(DATA_DIR / "forecast_graph_data.csv", index=False)

    best_model_key = metrics_df.iloc[0]["model_key"]
    best_model_name = metrics_df.iloc[0]["model_name"]

    api_payload = {
        "models": model_registry,
        "default_model_key": best_model_key,
        "default_model_name": best_model_name,
        "available_horizons": FORECAST_HORIZONS,
        "last_dataset_month": df["date_month"].max().strftime("%Y-%m-%d"),
        "vehicles": sorted(df["vehicle_model"].unique().tolist()),
        "graph_data": graph_df.to_dict(orient="records")
    }

    with open(DATA_DIR / "forecast_api_payload.json", "w", encoding="utf-8") as f:
        json.dump(api_payload, f, indent=2)

    with open(DATA_DIR / "model_registry.json", "w", encoding="utf-8") as f:
        json.dump(model_registry, f, indent=2)

    summary = {
        "dataset_rows": int(len(df)),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "train_end_cutoff": TRAIN_END_DATE,
        "best_model_key": best_model_key,
        "best_model_name": best_model_name,
        "available_models": metrics_df[["model_key", "model_name"]].to_dict(orient="records"),
        "available_horizons": FORECAST_HORIZONS,
        "model_dir": str(MODEL_DIR),
        "data_dir": str(DATA_DIR)
    }

    with open(DATA_DIR / "export_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n====================================")
    print("TRAINING AND EXPORT COMPLETE")
    print("====================================")
    print(metrics_df.to_string(index=False))
    print(f"\nBest model: {best_model_name} ({best_model_key})")
    print(f"Model files saved in: {MODEL_DIR}")
    print(f"Data files saved in: {DATA_DIR}")


# =========================================================
# 11. MAIN RUN
# =========================================================
if __name__ == "__main__":
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = load_and_prepare_dataset(DATASET_PATH)
    train_and_export(df)
