from app.services.gpt_explanation import generate_explanation_for_pair
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.prediction_service import predict_pair
from app.services.gpt_explanation import generate_explanation_for_pair
from app.db.database import engine
from app.services.get_ohlc_data import get_ohlc_data
from app.services.get_historic_validations import get_historic_validation_data

executor = ThreadPoolExecutor(max_workers=10)

app = FastAPI(
    title = "Volatility Radar"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    pair: str
    date: str

class ExplanationRequest(BaseModel):
    pair: str
    date: str

@app.get("/")
async def root():
    return { "message" : "Volatility Radar API is running now"}

@app.get("/health")
async def health():
    return {"Status" : "healthy"} 

@app.get("/pairs")
async def get_pairs():
    return ["EURUSD", "GBPUSD", "USDJPY"]

@app.post("/predict")
async def predict(request: PredictionRequest):
    return predict_pair(request.pair, request.date)

@app.post("/explain")
async def explain(request: ExplanationRequest):
    return generate_explanation_for_pair(request.pair, request.date)

@app.post("/ohlcdata")
async def get_data(request: PredictionRequest):
    return get_ohlc_data(request.pair, request.date)

@app.post("/historic_validation")
async def get_historic_validation(request: PredictionRequest):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        get_historic_validation_data,
        request.pair,
        request.date
    )

@app.get("/events")
async def get_events(pair: str, date: str):
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}
    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")

    pair_1 = pair[:3]
    pair_2 = pair[3:]

    q = f"""
    SELECT currency, event, impact
    FROM calendar_events
    WHERE currency IN ('{pair_1}', '{pair_2}')
    AND date = '{date}'
    ORDER BY 
        CASE impact 
            WHEN 'High' THEN 1 
            WHEN 'Medium' THEN 2 
            ELSE 3 
        END
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
    SELECT `date`, `open`, `high`, `low`, `close`
    FROM forex_prices
    WHERE pair = '{pair}'
    AND `date` >= DATE_SUB('{from_date}', INTERVAL {days} DAY)
    ORDER BY `date` ASC;
    """
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(executor, pd.read_sql, q, engine)
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")

from app.services.analytics_service import (
    get_overview,
    get_confusion_matrix,
    get_confidence_calibration,
    get_accuracy_trend,
    get_feature_importance
)

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