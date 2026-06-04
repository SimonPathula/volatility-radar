import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from app.services.prediction_service import predict_pair

app = FastAPI(
    title = "Volatility Radar"
)

class PredictionRequest(BaseModel):
    pair: str
    date: str

model = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")

@app.get("/")
def root():
    return { "message" : "Volatility Radar API is running now"}

@app.get("/health")
def health():
    return {"Status" : "healthy"} 

@app.get("/pairs")
def get_pairs():
    return ["EURUSD", "GBPUSD", "USDJPY"]

@app.post("/predict")
def predict(request: PredictionRequest):
    return predict_pair(request.pair, request.date)
