"""
app/services/price_refresher.py

Fetches FX prices from Alpha Vantage and upserts into forex_prices.
Used by:
  - nightly_update.py  (cron job, completed candles)
  - prediction_service.py  (on-demand, today's partial candle)
"""

import os
import logging
import requests
import pandas as pd
from io import StringIO
from datetime import date, timedelta
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

from app.db.database import engine

log = logging.getLogger(__name__)

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

PAIR_SYMBOLS = {
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
}


# ── One-time migration (safe to call repeatedly) ──────────────────────────────

def ensure_unique_constraint():
    check_sql = """
        SELECT COUNT(*) AS cnt
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'forex_prices'
          AND index_name = 'uniq_pair_date'
    """
    with engine.begin() as conn:
        row = conn.execute(text(check_sql)).fetchone()
        if row[0] == 0:
            # Deduplicate first — keep lowest id per (pair, date)
            conn.execute(text("""
                DELETE fp1 FROM forex_prices fp1
                INNER JOIN forex_prices fp2
                  ON fp1.pair = fp2.pair
                 AND fp1.date = fp2.date
                 AND fp1.id > fp2.id
            """))
            log.info("Deduplicated forex_prices")
            conn.execute(text(
                "ALTER TABLE forex_prices "
                "ADD UNIQUE KEY uniq_pair_date (pair, date)"
            ))
            log.info("Added UNIQUE KEY uniq_pair_date to forex_prices")
        else:
            log.debug("UNIQUE KEY uniq_pair_date already exists")


# ── Core fetch ────────────────────────────────────────────────────────────────

def _fetch_av_prices(from_symbol: str, to_symbol: str) -> pd.DataFrame:
    """
    Calls AV FX_DAILY (full output). Returns DataFrame with columns:
    [date, open, high, low, close]  — date as datetime.date
    """
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=FX_DAILY"
        f"&from_symbol={from_symbol}"
        f"&to_symbol={to_symbol}"
        f"&outputsize=full"
        f"&apikey={ALPHA_VANTAGE_KEY}"
        f"&datatype=csv"
    )

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    if "Error Message" in r.text or "Note" in r.text[:200]:
        raise ValueError(f"AV API error for {from_symbol}{to_symbol}: {r.text[:300]}")

    df = pd.read_csv(StringIO(r.text))
    df = df.rename(columns={"timestamp": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.date

    return df[["date", "open", "high", "low", "close"]]


# ── Upsert ────────────────────────────────────────────────────────────────────

def _upsert_prices(pair: str, df: pd.DataFrame):
    """
    Upserts rows into forex_prices using ON DUPLICATE KEY UPDATE.
    Requires UNIQUE KEY on (pair, date).
    """
    if df.empty:
        return

    sql = text("""
        INSERT INTO forex_prices (date, pair, open, high, low, close)
        VALUES (:date, :pair, :open, :high, :low, :close)
        ON DUPLICATE KEY UPDATE
            open  = VALUES(open),
            high  = VALUES(high),
            low   = VALUES(low),
            close = VALUES(close)
    """)

    records = [
        {
            "date":  str(row["date"]),
            "pair":  pair,
            "open":  float(row["open"]),
            "high":  float(row["high"]),
            "low":   float(row["low"]),
            "close": float(row["close"]),
        }
        for _, row in df.iterrows()
    ]

    with engine.begin() as conn:
        conn.execute(sql, records)

    log.info(f"Upserted {len(records)} rows for {pair}")


# ── Public API ────────────────────────────────────────────────────────────────

def refresh_prices_for_range(from_date: date, to_date: date):
    """
    Fetches and upserts prices for all 3 pairs within [from_date, to_date].
    Used by the nightly cron job.
    """
    for pair, (fs, ts) in PAIR_SYMBOLS.items():
        try:
            df = _fetch_av_prices(fs, ts)
            df = df[(df["date"] >= from_date) & (df["date"] <= to_date)]
            _upsert_prices(pair, df)
            log.info(f"{pair}: {len(df)} rows in range {from_date} → {to_date}")
        except Exception as e:
            log.error(f"Failed to refresh {pair}: {e}")


def ensure_today_candle():
    """
    Fetches today's partial candle from AV and upserts it.
    Called on-demand when a user requests a prediction for tomorrow
    (which needs today's candle as its feature row).

    Returns today's date if successful, raises on failure.
    """
    today = date.today()

    for pair, (fs, ts) in PAIR_SYMBOLS.items():
        try:
            df = _fetch_av_prices(fs, ts)
            # AV returns the latest available row first — could be today or last trading day
            today_row = df[df["date"] == today]

            if today_row.empty:
                # Market may not have opened yet or it's weekend — use latest available
                latest_row = df.head(1)
                log.warning(
                    f"{pair}: No row for today ({today}), "
                    f"using latest available: {latest_row.iloc[0]['date']}"
                )
                _upsert_prices(pair, latest_row)
            else:
                _upsert_prices(pair, today_row)

        except Exception as e:
            log.error(f"ensure_today_candle failed for {pair}: {e}")
            raise


def get_latest_db_date() -> date:
    """Returns MAX(date) from forex_prices."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "SELECT MAX(date) AS dt "
                "FROM forex_prices"
            )
        ).fetchone()
        
    if result[0] is None: return None

    return pd.to_datetime(result[0]).date()


def is_price_stale() -> bool:
    """
    Returns True if DB is missing completed candles.
    'Stale' means: latest_db_date < yesterday (on a weekday).
    Skips weekends — Friday's candle is the freshest valid candle over the weekend.
    """
    today = date.today()
    latest = get_latest_db_date()

    # Walk backwards to find last expected trading day
    expected = today - timedelta(days=1)
    while expected.weekday() >= 5:   # skip Sat=5, Sun=6
        expected -= timedelta(days=1)

    return latest < expected