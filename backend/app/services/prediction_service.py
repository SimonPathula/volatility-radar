import joblib
import pandas as pd
from datetime import timedelta
from app.db.database import engine
from fastapi import HTTPException
from app.services.prediction_core import build_prediction_features
from app.services.shap_explaination import get_top_shap_features

MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")

def get_actual_label(pair: str, date: str):

        q = f"""
        SELECT *
        FROM forex_prices
        WHERE pair = '{pair}'
        AND date <= '{date}'
        ORDER BY date DESC
        LIMIT 30
        """

        df = pd.read_sql(q, engine)

        if len(df) < 21:
            return None

        df = df.sort_values("date")

        df["daily_return"] = (
            (df["close"] - df["open"])
            * 100
            / df["open"]
        )

        df["rolling_std_20"] = (
            df["daily_return"]
            .rolling(20, min_periods=10)
            .std()
        )

        threshold = (
            0.35
            * df["rolling_std_20"].iloc[-1]
        )

        next_q = f"""
        SELECT *
        FROM forex_prices
        WHERE pair = '{pair}'
        AND date > '{date}'
        ORDER BY date
        LIMIT 1
        """

        next_day = pd.read_sql(next_q, engine)

        if next_day.empty:
            return None

        move = (
            (next_day.iloc[0]["close"]
            - next_day.iloc[0]["open"])
            * 100
            / next_day.iloc[0]["open"]
        )

        if move > threshold:
            return "Bullish"

        elif move < -threshold:
            return "Bearish"

        return "Neutral"
        
def predict_pair_past(pair:str, date:str):
    df = build_prediction_features(pair, date)

    feature_names = MODEL.feature_names_in_

    X = df[feature_names]

    prediction = MODEL.predict(X)[0]
    probabilities = MODEL.predict_proba(X)[0]

    top_features = get_top_shap_features(
    X,
    prediction
    )

    actual = get_actual_label(pair, date)

    LABEL_MAP = {
        0: "Bearish",
        1: "Neutral",
        2: "Bullish"
    }

    return {
    "pair": pair,
    "date": date,
    "prediction": LABEL_MAP[prediction],
    "actual": actual,
    "correct": (
        actual == LABEL_MAP[prediction]
        if actual is not None
        else None
    ),
    "confidence": float(probabilities.max()),
    "bearish_probability": float(probabilities[0]),
    "neutral_probability": float(probabilities[1]),
    "bullish_probability": float(probabilities[2]),
    "top_drivers" : top_features
    }

def predict_pair_future(pair:str, date:str):
    latest_price_date = pd.read_sql(
        f"SELECT MAX(date) AS dt FROM forex_prices",
        engine
    ).iloc[0]["dt"]

    df = build_prediction_features(
    pair,
    latest_price_date + timedelta(days=1)
    )

    feature_names = MODEL.feature_names_in_

    X = df[feature_names]

    prediction = MODEL.predict(X)[0]
    probabilities = MODEL.predict_proba(X)[0]

    top_features = get_top_shap_features(
        X,
        prediction
    )

    LABEL_MAP = {
        0: "Bearish",
        1: "Neutral",
        2: "Bullish"
    }

    return {
    "pair": pair,
    "prediction_for": str(
        pd.to_datetime(latest_price_date).date()
        + pd.Timedelta(days=1)
    ),
    "prediction": LABEL_MAP[prediction],
    "confidence": float(probabilities.max()),
    "bearish_probability": float(probabilities[0]),
    "neutral_probability": float(probabilities[1]),
    "bullish_probability": float(probabilities[2]),
    "top drivers" : top_features
    }

def predict_pair(pair:str, date:str):
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

        return predict_pair_past(pair, date)

    elif requested_date == latest_price_date + timedelta(days=1):

        result = predict_pair_future(pair, date)

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
