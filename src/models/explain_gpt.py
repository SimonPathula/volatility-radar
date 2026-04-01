import os
os.chdir("D:/Projects/volatility-radar")

from dotenv import load_dotenv
load_dotenv()

import shap
import joblib
import numpy as np
import pandas as pd

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PAIR_NAMES = {0: 'EURUSD', 1: 'GBPUSD', 2: 'USDJPY'}
LABEL_NAMES = {0: 'Bearish', 1: 'Neutral', 2: 'Bullish'}

FEATURE_COLS = [
    'pair', 'day_of_week', 'month', 'week_of_year', 'is_month_end', 'is_month_start',
    'max_up_pips', 'max_down_pips', 'max_profit', 'max_loss', 'daily_return',
    'return_3d', 'return_5d', 'return_10d', 'rolling_std_5', 'rolling_std_10',
    'rolling_std_20', 'rsi_14', 'atr_14', 'momentum_5d', 'momentum_10d',
    'dist_from_mean_20d', 'daily_range', 'candle_body', 'upper_wick', 'lower_wick',
    'high_impact_count', 'medium_impact_count', 'low_impact_count', 'max_z_score',
    'sum_signal', 'dominant_direction', 'max_surprise_z', 'sum_signal_surprise'
]

def build_prompt(pair, date, predicted_label, probabilities, top_shap_features):
    pair_name = PAIR_NAMES[pair]
    label_name = LABEL_NAMES[predicted_label]
    confidence = probabilities[label_name]

    features_text = "\n".join([
        f"- {f['feature']}: value={f['value']:.4f}, SHAP impact={f['shap_impact']:+.4f}"
        for f in top_shap_features
    ])

    prompt = f"""You are a professional forex analyst explaining a machine learning model's session bias prediction to a trader.

                Prediction details:
                - Pair: {pair_name}
                - Date: {date}
                - Predicted bias: {label_name}
                - Confidence: {confidence:.0%}
                - Probabilities: Bearish={probabilities['Bearish']:.0%}, Neutral={probabilities['Neutral']:.0%}, Bullish={probabilities['Bullish']:.0%}

                Top model drivers (SHAP values):
                {features_text}

                Write a 3-4 sentence explanation for a forex trader. Explain what the key drivers mean in market terms. Be direct and specific. Do not mention SHAP or machine learning — speak purely in trading language. End with one sentence on what to watch for."""

    return prompt


def get_gpt_explanation(pair, date, predicted_label, probabilities, top_shap_features):
    prompt = build_prompt(pair, date, predicted_label, probabilities, top_shap_features)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=200
    )

    return response.choices[0].message.content.strip()


# load
final_model = joblib.load('src/models/volatility_radar_xgb.pkl')
df = pd.read_csv('data/final_cleaned_data/full_features.csv')
df['date'] = pd.to_datetime(df['date'])

# pick a sample row — latest EURUSD date
sample = df[(df['pair'] == 0)].sort_values('date').iloc[-1]
sample_df = pd.DataFrame(sample[FEATURE_COLS].values.reshape(1, -1), columns=FEATURE_COLS).astype(float)

# predict
proba = final_model.predict_proba(sample_df)[0]
predicted_label = int(np.argmax(proba))
probabilities = {'Bearish': proba[0], 'Neutral': proba[1], 'Bullish': proba[2]}

# SHAP for this row
explainer = shap.TreeExplainer(final_model)
shap_vals = explainer(sample_df)

# top 5 SHAP features for predicted class
shap_for_class = shap_vals.values[0, :, predicted_label]
top_indices = np.argsort(np.abs(shap_for_class))[::-1][:5]
top_shap_features = [
    {
        'feature': FEATURE_COLS[i],
        'value': float(sample_df.iloc[0, i]),
        'shap_impact': float(shap_for_class[i])
    }
    for i in top_indices
]

# generate explanation
explanation = get_gpt_explanation(
    pair=int(sample['pair']),
    date=str(sample['date'].date()),
    predicted_label=predicted_label,
    probabilities=probabilities,
    top_shap_features=top_shap_features
)

print(f"Pair: {PAIR_NAMES[int(sample['pair'])]}")
print(f"Date: {sample['date'].date()}")
print(f"Prediction: {LABEL_NAMES[predicted_label]} ({probabilities[LABEL_NAMES[predicted_label]]:.0%} confidence)")
print(f"\nGPT-4o Explanation:\n{explanation}")