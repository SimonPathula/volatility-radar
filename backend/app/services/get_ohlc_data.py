import pandas as pd
from datetime import date as today_fn, timedelta
from fastapi import HTTPException
from app.db.database import engine
from app.services.price_refresher import ensure_today_candle


def ohlc(date: str, pair: str):
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
        "pair":  pair,
        "date":  date,
        "open":  df["open"].iloc[0],
        "high":  df["high"].iloc[0],
        "low":   df["low"].iloc[0],
        "close": df["close"].iloc[0],
    }


def get_ohlc_data(pair: str, date: str):
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
        return ohlc(date, pair)

    # Today
    elif requested_date == today:
        try:
            ensure_today_candle()
        except Exception:
            pass
        return ohlc(date, pair)

    # Tomorrow
    elif requested_date == tomorrow:
        try:
            ensure_today_candle()
        except Exception:
            pass
        result = ohlc(date, pair)
        if requested_date.weekday() >= 5:
            result["warning"] = (
                "Forex markets will be closed tomorrow. "
                "Market reopen gaps and abnormal price behavior may occur."
            )
        return result

    else:
        raise HTTPException(status_code=400, detail="Select a historical trading day or tomorrow.")