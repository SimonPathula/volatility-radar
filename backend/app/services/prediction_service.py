import joblib
import pandas as pd
from datetime import timedelta
from app.db.database import engine
from fastapi import HTTPException
from app.services.feature_pipeline import build_price_features, build_calendar_features, create_calendar_signals,aggregate_calendar_features, merge_features

MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")

def get_actual_label(pair: str, date: str):

        q = f"""
        SELECT *
        FROM forex_prices
        WHERE pair = '{pair}'
        AND date <= '{date}'
        ORDER BY date DESC
        LIMIT 40
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
    dt = pd.to_datetime(date)

    price_query = f'''
    SELECT *
    FROM forex_prices
    WHERE pair = "{pair}" AND `date` < '{dt}'
    ORDER BY `date` DESC
    LIMIT 30
    '''

    pair_1 = pair[:3]
    pair_2 = pair[3:]

    cal_query = f"""
    SELECT *
    FROM calendar_events
    WHERE currency IN ('{pair_1}','{pair_2}')
    AND `date` < '{dt}'
    ORDER BY `date` DESC
    """

    price_df = pd.read_sql(price_query, engine)
    price_df = price_df.sort_values("date")

    cal_df = pd.read_sql(cal_query, engine)
    cal_df = cal_df.sort_values("date")

    price_df = build_price_features(price_df)
    cal_df = build_calendar_features(cal_df)
    cal_df = create_calendar_signals(cal_df)
    merged = merge_features(price_df, cal_df)

    def generate_vector(df):
        return df.tail(1)

    df = generate_vector(merged)

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Not enough historical data available."
        )

    feature_names = MODEL.feature_names_in_

    pair_map = {
        'EURUSD': 0,
        'GBPUSD': 1,
        'USDJPY': 2
    }

    df['pair'] = df['pair'].map(pair_map)

    X = df[feature_names]

    prediction = MODEL.predict(X)[0]
    probabilities = MODEL.predict_proba(X)[0]

    actual = get_actual_label(pair, date)

    label_map = {
        0: "Bearish",
        1: "Neutral",
        2: "Bullish"
    }

    return {
    "pair": pair,
    "date": date,
    "prediction": label_map[prediction],
    "actual": actual,
    "correct": (
        actual == label_map[prediction]
        if actual is not None
        else None
    ),
    "confidence": float(probabilities.max()),
    "bearish_probability": float(probabilities[0]),
    "neutral_probability": float(probabilities[1]),
    "bullish_probability": float(probabilities[2])
    }

def predict_pair_future(pair:str, date:str):
    latest_price_date = pd.read_sql(
        f"SELECT MAX(date) AS dt FROM forex_prices",
        engine
    ).iloc[0]["dt"]

    price_query = f'''
    SELECT *
    FROM forex_prices
    WHERE pair = '{pair}'
    AND date <= '{latest_price_date}'
    ORDER BY `date` DESC
    LIMIT 30
    '''
    pair_1 = pair[:3]
    pair_2 = pair[3:]

    cal_query = f"""
    SELECT *
    FROM calendar_events
    WHERE currency IN ('{pair_1}','{pair_2}')
    AND `date` < '{latest_price_date}'
    ORDER BY `date` DESC
    """
    price_df = pd.read_sql(price_query, engine)
    price_df = price_df.sort_values("date")

    cal_df = pd.read_sql(cal_query, engine)
    cal_df = cal_df.sort_values("date")

    price_df = build_price_features(price_df)
    cal_df = build_calendar_features(cal_df)
    cal_df = create_calendar_signals(cal_df)
    merged = merge_features(price_df, cal_df)

    if merged.empty:
        raise ValueError(
            f"No data available for {pair}"
        )

    def generate_vector(df):
        return df.tail(1)

    df = generate_vector(merged)


    feature_names = MODEL.feature_names_in_

    pair_map = {
        'EURUSD': 0,
        'GBPUSD': 1,
        'USDJPY': 2
    }

    df['pair'] = df['pair'].map(pair_map)

    X = df[feature_names]

    prediction = MODEL.predict(X)[0]
    probabilities = MODEL.predict_proba(X)[0]

    label_map = {
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
    "prediction": label_map[prediction],
    "confidence": float(probabilities.max()),
    "bearish_probability": float(probabilities[0]),
    "neutral_probability": float(probabilities[1]),
    "bullish_probability": float(probabilities[2])
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
