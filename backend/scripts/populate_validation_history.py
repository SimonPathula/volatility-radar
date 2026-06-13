import joblib
import pandas as pd
import json
from app.db.database import engine
from app.services.prediction_service import predict_pair_past

MODEL = joblib.load(r"D:\projects\volatility-radar\src\models\volatility_radar_xgb.pkl")

VALID_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
LOOKBACK_DAYS = 180


def create_table():
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS model_validation_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pair VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                prediction VARCHAR(10) NOT NULL,
                actual VARCHAR(10) NOT NULL,
                confidence FLOAT NOT NULL,
                top_drivers JSON,
                UNIQUE KEY uniq_pair_date (pair, date)
            )
        """)


def collect_predictions(pair: str, lookback_days: int = LOOKBACK_DAYS):
    q = f"""
    SELECT date
    FROM forex_prices
    WHERE pair = '{pair}'
    ORDER BY date DESC
    LIMIT {lookback_days}
    """
    dates_df = pd.read_sql(q, engine)

    records = []
    for target_date in dates_df["date"]:
        try:
            result = predict_pair_past(pair, str(target_date))
        except Exception as e:
            print(f"  skip {pair} {target_date}: {e}")
            continue

        if result["actual"] is None:
            continue

        records.append({
            "pair": pair,
            "date": str(target_date),
            "prediction": result["prediction"],
            "actual": result["actual"],
            "confidence": result["confidence"],
            "top_drivers": json.dumps(result.get("top_drivers", []))
        })

    return records


def upsert_records(records):
    if not records:
        return

    with engine.begin() as conn:
        for r in records:
            conn.exec_driver_sql(
                """
                INSERT INTO model_validation_history
                    (pair, date, prediction, actual, confidence, top_drivers)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    prediction = VALUES(prediction),
                    actual = VALUES(actual),
                    confidence = VALUES(confidence),
                    top_drivers = VALUES(top_drivers)
                """,
                (r["pair"], r["date"], r["prediction"], r["actual"], r["confidence"], r["top_drivers"])
            )


def main():
    print("Creating table if not exists...")
    create_table()

    for pair in VALID_PAIRS:
        print(f"Processing {pair} (last {LOOKBACK_DAYS} days)...")
        records = collect_predictions(pair)
        print(f"  {len(records)} records computed")
        upsert_records(records)
        print(f"  upserted into model_validation_history")

    print("Done.")


if __name__ == "__main__":
    main()