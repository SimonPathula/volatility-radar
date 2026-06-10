from app.services.gpt_explanation import generate_explanation_for_pair
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from app.services.prediction_service import predict_pair
from app.services.gpt_explanation import generate_explanation_for_pair
from app.db.database import engine


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

@app.get("/prices/{pair}")
def get_prices(pair: str, days: int = 90):
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}
    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")
    q = f"""
    SELECT date, open, high, low, close
    FROM forex_prices
    WHERE pair = '{pair}'
    ORDER BY date DESC
    LIMIT {days}
    """
    df = pd.read_sql(q, engine)
    df = df.sort_values("date")
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")

@app.get("/backtest/{pair}")
def get_backtest(pair: str, days: int = 30):
    """Run last N predictions and return win/loss for profit simulation."""
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}
    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")
    q = f"""
    SELECT date FROM forex_prices
    WHERE pair = '{pair}'
    ORDER BY date DESC
    LIMIT {days + 1}
    """
    dates_df = pd.read_sql(q, engine)
    dates_df = dates_df.sort_values("date")
    # Skip last row (need next-day actual for it)
    trade_dates = dates_df["date"].tolist()[:-1]
    results = []
    for d in trade_dates:
        try:
            pred = predict_pair(pair, str(d))
            results.append({
                "date": str(d),
                "prediction": pred.get("prediction"),
                "actual": pred.get("actual"),
                "correct": pred.get("correct"),
                "confidence": pred.get("confidence"),
            })
        except Exception:
            continue
    return results