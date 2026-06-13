import json
import pandas as pd
from collections import defaultdict
from app.db.database import engine

LABEL_ORDER = ["Bearish", "Neutral", "Bullish"]


def _load_records(lookback_days: int = 180):
    """
    Reads precomputed validation history from the model_validation_history table.
    This table is populated by app/scripts/populate_validation_history.py.
    """
    q = f"""
    SELECT pair, date, prediction, actual, confidence, top_drivers
    FROM model_validation_history
    ORDER BY date DESC
    LIMIT {lookback_days * 3}
    """
    df = pd.read_sql(q, engine)

    records = []
    for _, row in df.iterrows():
        top_drivers = row["top_drivers"]
        if isinstance(top_drivers, str):
            try:
                top_drivers = json.loads(top_drivers)
            except (ValueError, TypeError):
                top_drivers = []
        elif top_drivers is None:
            top_drivers = []

        records.append({
            "date": str(row["date"]),
            "pair": row["pair"],
            "prediction": row["prediction"],
            "actual": row["actual"],
            "confidence": float(row["confidence"]),
            "top_drivers": top_drivers
        })

    return records


def get_overview(lookback_days: int = 180):
    records = _load_records(lookback_days)

    if not records:
        return {
            "overall_accuracy": 0,
            "macro_f1": 0,
            "precision": {"Bullish": 0, "Bearish": 0, "Neutral": 0},
            "recall": {"Bullish": 0, "Bearish": 0, "Neutral": 0},
            "total_predictions": 0
        }

    total = len(records)
    correct = sum(1 for r in records if r["prediction"] == r["actual"])
    overall_accuracy = round(correct / total * 100, 1)

    precision = {}
    recall = {}
    f1_scores = {}

    for label in LABEL_ORDER:
        tp = sum(1 for r in records if r["prediction"] == label and r["actual"] == label)
        fp = sum(1 for r in records if r["prediction"] == label and r["actual"] != label)
        fn = sum(1 for r in records if r["prediction"] != label and r["actual"] == label)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

        precision[label] = round(prec * 100, 1)
        recall[label] = round(rec * 100, 1)
        f1_scores[label] = f1

    macro_f1 = round(sum(f1_scores.values()) / len(f1_scores) * 100, 1)

    return {
        "overall_accuracy": overall_accuracy,
        "macro_f1": macro_f1,
        "precision": precision,
        "recall": recall,
        "total_predictions": total
    }


def get_confusion_matrix(lookback_days: int = 180):
    records = _load_records(lookback_days)

    matrix = {actual: {pred: 0 for pred in LABEL_ORDER} for actual in LABEL_ORDER}

    for r in records:
        matrix[r["actual"]][r["prediction"]] += 1

    return {
        "labels": LABEL_ORDER,
        "matrix": matrix,
        "total": len(records)
    }


def get_confidence_calibration(lookback_days: int = 180):
    records = _load_records(lookback_days)

    buckets = [
        (0.30, 0.40, "30-40%"),
        (0.40, 0.50, "40-50%"),
        (0.50, 0.60, "50-60%"),
        (0.60, 0.70, "60-70%"),
        (0.70, 0.80, "70-80%"),
        (0.80, 1.01, "80-100%"),
    ]

    result = []
    for low, high, label in buckets:
        bucket_records = [r for r in records if low <= r["confidence"] < high]
        if not bucket_records:
            result.append({"bucket": label, "accuracy": None, "count": 0})
            continue

        correct = sum(1 for r in bucket_records if r["prediction"] == r["actual"])
        accuracy = round(correct / len(bucket_records) * 100, 1)
        result.append({"bucket": label, "accuracy": accuracy, "count": len(bucket_records)})

    return result


def get_accuracy_trend(lookback_days: int = 180):
    records = _load_records(lookback_days)

    monthly = defaultdict(lambda: {"correct": 0, "total": 0})

    for r in records:
        month_key = r["date"][:7]
        monthly[month_key]["total"] += 1
        if r["prediction"] == r["actual"]:
            monthly[month_key]["correct"] += 1

    trend = []
    for month_key in sorted(monthly.keys()):
        stats = monthly[month_key]
        accuracy = round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        trend.append({
            "month": month_key,
            "accuracy": accuracy,
            "total_predictions": stats["total"]
        })

    return trend


def get_feature_importance(lookback_days: int = 180, top_n: int = 8):
    records = _load_records(lookback_days)

    feature_impacts = defaultdict(list)

    for r in records:
        for d in r["top_drivers"]:
            feature_impacts[d["feature"]].append(abs(d["shap_impact"]))

    aggregated = []
    for feature, impacts in feature_impacts.items():
        aggregated.append({
            "feature": feature,
            "avg_abs_impact": round(sum(impacts) / len(impacts), 4),
            "appearances": len(impacts)
        })

    aggregated.sort(key=lambda x: x["avg_abs_impact"], reverse=True)

    return aggregated[:top_n]