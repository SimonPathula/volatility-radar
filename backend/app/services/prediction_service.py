"""
app/services/prediction_service.py

Semantics: "Predict for day X" uses day X's candle + day X's calendar events.
build_prediction_features(pair, cutoff_date=X+1) pulls `date < X+1` → includes X.

Date routing:

  requested_date    action
  ────────────────  ──────────────────────────────────────────────────────
  past weekday      predict using X's completed candle (already in DB)
  today             predict using today's completed candle (in DB after 3:30am cron)
  tomorrow          ensure_today_candle() → fetch tomorrow's partial from AV → predict
  weekend/far fut   reject
"""

import joblib
import pandas as pd
from datetime import date, timedelta
from fastapi import HTTPException
from app.db.database import engine
from app.services.prediction_core import build_prediction_features
from app.services.shap_explaination import get_top_shap_features
from app.services.price_refresher import (
    ensure_today_candle,
    is_price_stale,
    refresh_prices_for_range,
    get_latest_db_date,
)

MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")

VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}

LABEL_MAP = {0: "Bearish", 1: "Neutral", 2: "Bullish"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_actual_label(pair: str, target_date: str):
    """
    Actual label for target_date = next trading day's move vs rolling_std_20.
    Returns None if next-day candle not in DB yet.
    """
    q = f"""
    SELECT * 
    FROM forex_prices
    WHERE pair = '{pair}' 
    AND date <= '{target_date}'
    ORDER BY date DESC 
    LIMIT 30
    """
    df = pd.read_sql(q, engine)
    if len(df) < 21:
        return None

    df = df.sort_values("date")
    df["daily_return"]   = (df["close"] - df["open"]) * 100 / df["open"]
    df["rolling_std_20"] = df["daily_return"].rolling(20, min_periods=10).std()
    threshold = 0.35 * df["rolling_std_20"].iloc[-1]

    next_q = f"""
    SELECT * 
    FROM forex_prices
    WHERE pair = '{pair}' 
    AND date > '{target_date}'
    ORDER BY date ASC 
    LIMIT 1
    """
    next_day = pd.read_sql(next_q, engine)
    if next_day.empty:
        return None

    move = (next_day.iloc[0]["close"] - next_day.iloc[0]["open"]) * 100 / next_day.iloc[0]["open"]
    if move > threshold:  
        return "Bullish"
    if move < -threshold: 
        return "Bearish"
    return "Neutral"


def _run_model(pair: str, predict_for: date) -> dict:
    """
    Runs model for predict_for date.

    build_prediction_features()
    handles the cutoff internally so that
    predict_for's candle is included.
    """
    # cutoff = predict_for + timedelta(days=1)
    df = build_prediction_features(pair, predict_for)

    feature_names = MODEL.feature_names_in_
    X = df[feature_names]

    prediction    = MODEL.predict(X)[0]
    probabilities = MODEL.predict_proba(X)[0]
    top_features  = get_top_shap_features(X, prediction)

    return {
        "prediction":          LABEL_MAP[prediction],
        "confidence":          float(probabilities.max()),
        "bearish_probability": float(probabilities[0]),
        "neutral_probability": float(probabilities[1]),
        "bullish_probability": float(probabilities[2]),
        "top_drivers":         top_features,
    }


# ── Past prediction (actual known or knowable) ────────────────────────────────

def predict_pair_past(pair: str, target_date: str) -> dict:
    predict_for = pd.to_datetime(target_date).date()
    result = _run_model(pair, predict_for)
    actual = get_actual_label(pair, target_date)

    return {
        "pair":    pair,
        "date":    target_date,
        **result,
        "actual":  actual,
        "correct": (actual == result["prediction"] if actual is not None else None),
    }


# ── Future prediction (today or tomorrow, no actual yet) ─────────────────────

def predict_pair_future(pair: str, predict_for: date) -> dict:
    result = _run_model(pair, predict_for)

    return {
        "pair":           pair,
        "prediction_for": str(predict_for),
        "actual":         None,
        "correct":        None,
        **result,
    }


# ── Main router ───────────────────────────────────────────────────────────────

def predict_pair(pair: str, date_str: str) -> dict:

    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")

    requested = pd.to_datetime(date_str).date()
    today     = date.today()
    tomorrow  = today + timedelta(days=1)

    # Reject weekends
    if requested < today and requested.weekday() >= 5:
        raise HTTPException(
            status_code=400,
            detail="Forex markets are closed on weekends. Select a weekday"
        )

    # Reject far future
    if requested > tomorrow:
        raise HTTPException(
            status_code=400,
            detail="Only historical dates, today, and tomorrow are supported."
        )

    # Past date — X's candle should be in DB (cron keeps it fresh)
    if requested < today:
        if is_price_stale():
            try:
                latest = get_latest_db_date()

                refresh_prices_for_range(
                    latest + timedelta(days=1),
                    today
                )
            except Exception:
                pass
        return predict_pair_past(pair, date_str)

    # Today — today's candle should be in DB after 3:30am cron
    # If cron hasn't run yet (user is early), auto-refresh
    if requested == today:
        latest = get_latest_db_date()
        if latest < today:
            # Cron hasn't run yet today — fetch today's candle on demand
            try:
                ensure_today_candle()
            except Exception:
                pass  # predict with whatever we have
        return predict_pair_future(pair, today)

    # Tomorrow prediction uses the latest available candle.
    # ensure_today_candle() fetches today's candle if missing.
    if requested == tomorrow:
        try:
            ensure_today_candle()
        except Exception:
            pass

        result = predict_pair_future(pair, tomorrow)

        if tomorrow.weekday() >= 5:
            result["warning"] = (
                "Forex markets will be closed tomorrow. "
                "Market reopen gaps and abnormal price behaviour may occur."
            )

        return result