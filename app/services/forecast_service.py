import joblib
import pandas as pd
from datetime import datetime

# load once (IMPORTANT for performance)
MODEL_PATH = "C:\Users\charles\OneDrive\Documents\SofdesProject\app\model\random_forest_bundle.pkl"
model = joblib.load(MODEL_PATH)


def generate_forecast(vehicle, months):

    # Example input structure
    future = pd.DataFrame({
        "vehicle": [vehicle] * months,
        "step": list(range(1, months + 1))
    })

    preds = model.predict(future)

    dates = pd.date_range(
        start=datetime.today(),
        periods=months,
        freq="MS"
    )

    result = [
        {
            "date": str(d.date()),
            "forecast": float(p)
        }
        for d, p in zip(dates, preds)
    ]

    return result