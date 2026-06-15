import pandas as pd
from datetime import date as today_fn, timedelta
from fastapi.exceptions import HTTPException
from app.db.database import engine
from app.services.prediction_service import predict_pair_past


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
        prediction_result = predict_pair_past(pair, str(target_date))
        if prediction_result["actual"] is None:
            continue
        results.append(prediction_result["prediction"] == prediction_result["actual"])

    total = len(results)
    correct_count = sum(results)

    return {
        "pair": pair,
        "accuracy": round(correct_count / total * 100, 2) if total > 0 else 0,
        "correct_predictions": correct_count,
        "total_predictions": total,
    }


def get_historic_validation_data(pair: str, date: str):
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}

    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")

    requested_date = pd.to_datetime(date).date()
    today = today_fn.today()
    tomorrow = today + timedelta(days=1)

    # Past
    if requested_date < today:
        if requested_date.weekday() >= 5:
            raise HTTPException(status_code=400, detail="Forex market closed on weekends.")
        return get_hist_val_data(pair, date)

    # Today
    elif requested_date == today:
        return get_hist_val_data(pair, date)

    # Tomorrow
    elif requested_date == tomorrow:
        result = get_hist_val_data(pair, date)
        if requested_date.weekday() >= 5:
            result["warning"] = (
                "Forex markets will be closed tomorrow. "
                "Market reopen gaps and abnormal price behavior may occur."
            )
        return result

    else:
        raise HTTPException(status_code=400, detail="Select a historical trading day or tomorrow.")