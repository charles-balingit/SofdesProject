from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def load_sales_data():
    path = DATA_DIR / "sales_forecast_graph_data.csv"
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["month"])
    return df

def load_parts_forecast_data():
    path = DATA_DIR / "parts_forecast_graph_data.csv"
    df = pd.read_csv(path)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

def load_parts_actions_data():
    path = DATA_DIR / "recommended_actions_latest.csv"
    df = pd.read_csv(path)
    df["forecast_date"] = pd.to_datetime(df["forecast_date"])
    return df

def get_vehicle_models():
    df = load_sales_data()
    return sorted(df["vehicle_model"].dropna().unique().tolist())

def get_parts_list():
    df = load_parts_forecast_data()
    parts = (
        df[["part_id", "part_name"]]
        .drop_duplicates()
        .sort_values("part_name")
        .to_dict(orient="records")
    )
    return parts
