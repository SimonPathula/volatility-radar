from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from app.services.prediction_service import predict_pair
from app.services.gpt_explanation import generate_explanation_for_pair
from app.db.database import engine
from app.services.get_ohlc_data import get_ohlc_data
from app.services.get_historic_validations import get_historic_validation_data
from app.services.price_refresher import (
    ensure_unique_constraint,
    is_price_stale,
    refresh_prices_for_range,
    get_latest_db_date,
)
from app.services.analytics_service import (
    get_overview,
    get_confusion_matrix,
    get_confidence_calibration,
    get_accuracy_trend,
    get_feature_importance,
)

log = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=10)

app = FastAPI(title="Volatility Radar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://volatility-radar.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """
    On every cold start:    
    1. Ensure DB unique constraints exist
    2. Auto-refresh prices if stale (catches missed cron runs or fresh deploys)
    """
    loop = asyncio.get_event_loop()

    await loop.run_in_executor(executor, ensure_unique_constraint)

    stale = await loop.run_in_executor(executor, is_price_stale)

    if stale:
        log.info("Prices are stale on startup — refreshing now")

        today = date.today()

        latest = await loop.run_in_executor(
            executor,
            get_latest_db_date
        )

        if latest is not None and latest < today:
            from_date = latest + timedelta(days=1)
            if from_date <= today:
                await loop.run_in_executor(
                    executor,
                    refresh_prices_for_range,
                    from_date,
                    today,
                )

            log.info(
                f"Startup refresh completed "
                f"({latest + timedelta(days=1)} → {today})"
            )
    else:
        latest = await loop.run_in_executor(
            executor,
            get_latest_db_date
        )

        log.info(
            f"Prices are fresh. Latest date in DB: {latest}"
        )


# ── Schemas ───────────────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    pair: str
    date: str

class ExplanationRequest(BaseModel):
    pair: str
    date: str


# ── Health / meta ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Volatility Radar API is running"}

@app.get("/health")
async def health():
    latest = await asyncio.get_event_loop().run_in_executor(executor, get_latest_db_date)
    return {
        "status": "healthy",
        "latest_price_date": str(latest),
        "stale": await asyncio.get_event_loop().run_in_executor(executor, is_price_stale),
    }

@app.get("/pairs")
async def get_pairs():
    return ["EURUSD", "GBPUSD", "USDJPY"]


#Admin 

@app.get("/admin/refresh")
async def manual_refresh():
    """
    Manually trigger a price refresh.
    Useful after a missed cron job or during development.
    """
    today = date.today()
    loop = asyncio.get_event_loop()
    latest = await loop.run_in_executor(
        executor,
        get_latest_db_date
    )

    if latest is not None and latest < today:

        await loop.run_in_executor(
            executor,
            refresh_prices_for_range,
            latest + timedelta(days=1),
            today,
        )
    return {"status": "refreshed", "latest_price_date": str(latest)}


# ── Prediction & Explanation ──────────────────────────────────────────────────

@app.post("/predict")
async def predict(request: PredictionRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, predict_pair, request.pair, request.date)

@app.post("/explain")
async def explain(request: ExplanationRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor, generate_explanation_for_pair, request.pair, request.date
    )


# ── OHLC & Historic Validation ────────────────────────────────────────────────

@app.post("/ohlcdata")
async def get_data(request: PredictionRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_ohlc_data, request.pair, request.date)

@app.post("/historic_validation")
async def get_historic_validation(request: PredictionRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor, get_historic_validation_data, request.pair, request.date
    )


# ── Events & Prices ───────────────────────────────────────────────────────────

@app.get("/events")
async def get_events(pair: str, date: str):
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}
    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")

    pair_1, pair_2 = pair[:3], pair[3:]
    q = f"""
    SELECT currency, event, impact
    FROM calendar_events
    WHERE currency IN ('{pair_1}', '{pair_2}')
    AND date = '{date}'
    ORDER BY CASE impact WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
    """
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(executor, pd.read_sql, q, engine)
    return df.to_dict(orient="records")

@app.get("/prices/{pair}")
async def get_prices(pair: str, from_date: str = None, days: int = 90):
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}
    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")

    q = f"""
    SELECT "date", "open", "high", "low", "close"
    FROM forex_prices
    WHERE pair = '{pair}'
    AND "date" >= '{from_date}'::date - INTERVAL '{days} days'
    ORDER BY "date" ASC
    """
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(executor, pd.read_sql, q, engine)
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.get("/analytics/overview")
async def analytics_overview(lookback_days: int = 180):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_overview, lookback_days)

@app.get("/analytics/confusion_matrix")
async def analytics_confusion_matrix(lookback_days: int = 180):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_confusion_matrix, lookback_days)

@app.get("/analytics/confidence_calibration")
async def analytics_confidence_calibration(lookback_days: int = 180):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_confidence_calibration, lookback_days)

@app.get("/analytics/accuracy_trend")
async def analytics_accuracy_trend(lookback_days: int = 180):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_accuracy_trend, lookback_days)

@app.get("/analytics/feature_importance")
async def analytics_feature_importance(lookback_days: int = 180):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_feature_importance, lookback_days)