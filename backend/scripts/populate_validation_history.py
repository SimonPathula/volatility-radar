import joblib
import pandas as pd
import json
from pathlib import Path
from app.db.database import engine
from sqlalchemy import text
from app.services.prediction_service import predict_pair_past
import logging
log = logging.getLogger(__name__)

MODEL_PATH = (
    Path(__file__).resolve().parents[1]/"models"/"volatility_radar_xgb.pkl"
)

MODEL = joblib.load(MODEL_PATH)

VALID_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
LOOKBACK_DAYS = 180


def create_table():
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS model_validation_history (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                prediction VARCHAR(10) NOT NULL,
                actual VARCHAR(10) NOT NULL,
                confidence FLOAT NOT NULL,
                top_drivers JSON,
                CONSTRAINT uniq_pair_date UNIQUE (pair, date)
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
    total = len(dates_df)
    for i, target_date in enumerate(dates_df["date"], 1):
        try:
            if i % 10 == 0 or i == 1:
                log.info(f"{pair}: {i}/{total} ({round(i/total*100)}%)")
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
            conn.execute(
                text("""
                    INSERT INTO model_validation_history
                    (pair, date, prediction, actual, confidence, top_drivers)
                    VALUES
                    (:pair, :date, :prediction, :actual, :confidence, :top_drivers)

                    ON CONFLICT (pair, date)
                    DO UPDATE SET
                        prediction = EXCLUDED.prediction,
                        actual = EXCLUDED.actual,
                        confidence = EXCLUDED.confidence,
                        top_drivers = EXCLUDED.top_drivers
                """),
                r
            )

def update_validation_history():

    create_table()

    for pair in VALID_PAIRS:

        q = f"""
        SELECT MAX(date) AS dt
        FROM model_validation_history
        WHERE pair = '{pair}'
        """

        latest_val_date = pd.read_sql(
            q,
            engine
        ).iloc[0]["dt"]

        if pd.isna(latest_val_date):

            records = collect_predictions(
                pair,
                LOOKBACK_DAYS
            )

            upsert_records(records)

            continue

        price_dates = pd.read_sql(
            f"""
            SELECT date
            FROM forex_prices
            WHERE pair = '{pair}'
            AND date > '{latest_val_date}'
            ORDER BY date
            """,
            engine
        )

        records = []

        total_dates = len(price_dates)
        for i, target_date in enumerate(price_dates["date"], 1):

            try:
                if i % 10 == 0 or i == 1:
                    log.info(f"{pair}: processing {i}/{total_dates} ({round(i/total_dates*100)}%)")

                result = predict_pair_past(
                    pair,
                    str(target_date)
                )

                if result["actual"] is None:
                    continue

                records.append({
                    "pair": pair,
                    "date": str(target_date),
                    "prediction": result["prediction"],
                    "actual": result["actual"],
                    "confidence": result["confidence"],
                    "top_drivers": json.dumps(
                        result.get(
                            "top_drivers",
                            []
                        )
                    )
                })

            except Exception as e:

                print(
                    f"skip {pair} "
                    f"{target_date}: {e}"
                )

        upsert_records(records)


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