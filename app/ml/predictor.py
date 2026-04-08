import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "model" / "sales_random_forest_bundle.pkl"

# load once (FAST)
bundle = joblib.load(MODEL_PATH)


def generate_forecast(vehicle: str, months: int):

    history = bundle.history_by_vehicle[vehicle]
    last_date = datetime.strptime(
        bundle.last_date_by_vehicle[vehicle],
        "%Y-%m-%d"
    )

    results = []

    for i in range(months):

        next_date = last_date + relativedelta(months=i+1)

        # create empty feature row
        row = pd.DataFrame(
            [[0]*len(bundle.feature_columns)],
            columns=bundle.feature_columns
        )

        # activate vehicle column
        col = f"vehicle_model_{vehicle}"
        if col in row.columns:
            row[col] = 1

        pred = bundle.estimator.predict(row)[0]

        results.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "forecast": round(float(pred), 2)
        })

    return results
