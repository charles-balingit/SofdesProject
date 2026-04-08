from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_sales_data():
    path = DATA_DIR / "sales_forecast_graph_data.csv"
    df = pd.read_csv(path)

    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce")

    return df


def load_parts_forecast_data():
    path = DATA_DIR / "parts_forecast_graph_data.csv"
    df = pd.read_csv(path)

    if "forecast_date" in df.columns:
        df["forecast_date"] = pd.to_datetime(df["forecast_date"], errors="coerce")

    return df


def load_parts_actions_data():
    path = DATA_DIR / "recommended_actions_latest.csv"
    df = pd.read_csv(path)

    if "forecast_date" in df.columns:
        df["forecast_date"] = pd.to_datetime(df["forecast_date"], errors="coerce")

    return df


def get_vehicle_models():
    df = load_sales_data()

    if "vehicle_model" not in df.columns:
        return []

    models = (
        df["vehicle_model"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    return models


def get_parts_list():
    df = load_parts_forecast_data()

    if "part_id" not in df.columns or "part_name" not in df.columns:
        return []

    parts = (
        df[["part_id", "part_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("part_name")
        .to_dict(orient="records")
    )
    return parts
