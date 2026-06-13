import pandas as pd
from fastapi import HTTPException
from app.db.database import engine
from app.services.feature_pipeline import (
    build_price_features,
    build_calendar_features,
    create_calendar_signals,
    merge_features
)

PAIR_MAP = {
    "EURUSD": 0,
    "GBPUSD": 1,
    "USDJPY": 2
}


def build_prediction_features(pair, cutoff_date):

    pair_1 = pair[:3]
    pair_2 = pair[3:]

    price_query = f"""
    SELECT *
    FROM forex_prices
    WHERE pair = '{pair}'
    AND date < '{cutoff_date}'
    ORDER BY date DESC
    LIMIT 30
    """

    cal_query = f"""
    SELECT *
    FROM calendar_events
    WHERE currency IN ('{pair_1}','{pair_2}')
    AND date < '{cutoff_date}' 
    ORDER BY date DESC
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
        raise HTTPException(
            status_code=400,
            detail="Not enough historical data available."
        )

    df = merged.tail(1).copy()

    df["pair"] = df["pair"].map(PAIR_MAP)

    return df