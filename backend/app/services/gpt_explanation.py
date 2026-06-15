from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()
import os
import joblib
import pandas as pd
from datetime import timedelta
from app.db.database import engine
from datetime import date as date_today_fn, timedelta
from app.services.prediction_core import build_prediction_features
from app.services.shap_explaination import get_top_shap_features

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PAIR_MAP = {0: 'EURUSD', 1: 'GBPUSD', 2: 'USDJPY'}
LABEL_MAP = {0: 'Bearish', 1: 'Neutral', 2: 'Bullish'}
MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")
FEATURE_NAMES = MODEL.feature_names_in_


def build_prompt(pair, date, predicted_label, probabilities, top_shap_features):
    label_name = LABEL_MAP[predicted_label]
    confidence = probabilities[label_name]

    features_text = "\n".join([
        f"- {f['feature']}: value={f['value']:.4f}, SHAP impact={f['shap_impact']:+.4f}"
        for f in top_shap_features
    ])

    return f"""You are a professional forex analyst explaining a machine learning model's session bias prediction to a trader.

Prediction details:
- Pair: {pair}
- Date: {date}
- Predicted bias: {label_name}
- Confidence: {confidence:.0%}
- Probabilities: Bearish={probabilities['Bearish']:.0%}, Neutral={probabilities['Neutral']:.0%}, Bullish={probabilities['Bullish']:.0%}

Top model drivers (SHAP values):
{features_text}

Write a 3-4 sentence explanation for a forex trader. Explain what the key drivers mean in market terms. Be direct and specific. Do not mention SHAP or machine learning — speak purely in trading language. End with one sentence on what to watch for.

Only discuss information directly implied by the provided drivers. Do not invent market narratives, seasonality patterns, or macroeconomic events that are not provided."""


def get_gpt_explanation(pair, date, predicted_label, probabilities, top_shap_features):
    prompt = build_prompt(pair, date, predicted_label, probabilities, top_shap_features)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def generate_explanation(pair, date):
    df = build_prediction_features(pair, date)
    X = df[FEATURE_NAMES]

    prediction    = MODEL.predict(X)[0]
    probabilities = MODEL.predict_proba(X)[0]
    top_features  = get_top_shap_features(X, prediction)

    prob_dict = {
        "Bearish": float(probabilities[0]),
        "Neutral": float(probabilities[1]),
        "Bullish": float(probabilities[2]),
    }

    explanation = get_gpt_explanation(
        pair=pair,
        date=date,
        predicted_label=prediction,
        probabilities=prob_dict,
        top_shap_features=top_features,
    )

    return {
        "pair":        pair,
        "date":        date,
        "prediction":  LABEL_MAP[prediction],
        "explanation": explanation,
    }



def generate_explanation_for_pair(pair: str, date: str):
    VALID_PAIRS = {"EURUSD", "GBPUSD", "USDJPY"}

    if pair not in VALID_PAIRS:
        raise HTTPException(status_code=400, detail=f"Unsupported pair: {pair}")

    requested_date = pd.to_datetime(date).date()
    today = date_today_fn.today()
    tomorrow = today + timedelta(days=1)

    # Reject weekends for past dates
    if requested_date < today:
        if requested_date.weekday() >= 5:
            raise HTTPException(status_code=400, detail="Forex market closed on weekends.")
        return generate_explanation(pair, date)

    # Today
    elif requested_date == today:
        return generate_explanation(pair, date)

    # Tomorrow
    elif requested_date == tomorrow:
        result = generate_explanation(pair, date)
        if requested_date.weekday() >= 5:
            result["warning"] = (
                "Forex markets will be closed tomorrow. "
                "Market reopen gaps and abnormal price behavior may occur."
            )
        return result

    else:
        raise HTTPException(status_code=400, detail="Select a historical trading day or tomorrow.")