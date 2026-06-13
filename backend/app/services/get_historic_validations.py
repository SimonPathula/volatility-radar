import joblib
import pandas as pd
from datetime import timedelta
from app.db.database import engine 
from fastapi.exceptions import HTTPException
from app.services.prediction_service import predict_pair_past

MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")

def get_hist_val_data(pair: str, date: str):

    q = f"""
    SELECT date
    FROM forex_prices
    WHERE pair = '{pair}'
    AND date < '{date}'
    ORDER BY date DESC
    LIMIT 30
    """

    dates_df = pd.read_sql(q, engine)

    results = []

    for target_date in dates_df["date"]:

        prediction_result = predict_pair_past(
            pair,
            str(target_date)
        )

        correct = (
            prediction_result["prediction"]
            == prediction_result["actual"]
        )

        results.append(correct)

    total = len(results)
    correct_count = sum(results)

    accuracy = (
        correct_count / total * 100
        if total > 0
        else 0
    )

    return {
        "pair": pair,
        "accuracy": round(accuracy, 2),
        "correct_predictions": correct_count,
        "total_predictions": total
    }

def get_historic_validation_data(pair:str, date:str):
    VALID_PAIRS = {
        "EURUSD",
        "GBPUSD",
        "USDJPY"
    }
    
    if pair not in VALID_PAIRS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported pair: {pair}"
        )

    requested_date = pd.to_datetime(date).date()
    latest_price_date = pd.read_sql(
        "SELECT MAX(date) AS dt FROM forex_prices",
        engine
    ).iloc[0]["dt"]
 
    latest_price_date = pd.to_datetime(
        latest_price_date
    ).date()

    if requested_date < latest_price_date:

        if requested_date.weekday() >= 5:
            raise HTTPException(
            status_code=400,
            detail="Forex market closed on weekends."
        )

        return get_hist_val_data(pair, date)

    elif requested_date == latest_price_date + timedelta(days=1):

        result = get_hist_val_data(pair, date)

        if requested_date.weekday() >= 5:
            result["warning"] = (
                "Forex markets will be closed tomorrow. "
                "Market reopen gaps and abnormal price "
                "behavior may occur."
            )

        return result

    else:
        raise HTTPException(
        status_code=400,
        detail="Select a historical trading day or tomorrow."
    )