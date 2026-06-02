import joblib
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title = "Volatility Radar"
)

class PredictionRequest(BaseModel):
    pair: str

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
    return {
        "pair" : request.pair,
        "message" : "Model loaded successfully"
    }
