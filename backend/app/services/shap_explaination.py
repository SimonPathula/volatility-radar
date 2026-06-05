import shap
import joblib
import numpy as np

MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")
EXPLAINER = shap.TreeExplainer(MODEL)

def get_top_shap_features(X, predicted_label, top_n=5):


    shap_values = EXPLAINER(X)

    shap_for_class = (shap_values.values[0, :, predicted_label])

    top_idx = np.argsort(
        np.abs(shap_for_class)
    )[::-1][:top_n]

    features = []

    for i in top_idx:

        features.append({
            "feature": X.columns[i],
            "value": float(X.iloc[0, i]),
            "shap_impact": float(
                shap_for_class[i]
            )
        })

    return features