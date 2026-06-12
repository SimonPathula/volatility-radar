import pandas as pd
from datetime import timedelta
from fastapi import HTTPException
from app.db.database import engine

def ohlc(date:str, pair:str):
    pair_1 = pair[:3]
    pair_2 = pair[3:]

    price_query = f"""
    SELECT *
    FROM forex_prices
    WHERE pair = '{pair}'
    AND date <= '{date}'
    ORDER BY date DESC
    LIMIT 1
    """
    df = pd.read_sql(price_query, engine)

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.rename(columns={'timestamp': 'date'})

    df['date'] = pd.to_datetime(df['date'])

    return {
        "date" : date,
        "open" : df["open"].iloc[0],
        "high" : df["high"].iloc[0],
        "low" : df["low"].iloc[0],
        "close" : df["close"].iloc[0]
    }

def get_ohlc_data(pair: str, date:str):
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

        return ohlc(date, pair)

    elif requested_date == latest_price_date + timedelta(days=1):

        result = ohlc(date, pair)

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

