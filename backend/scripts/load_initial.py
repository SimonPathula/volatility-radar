import pandas as pd
from sqlalchemy import text

# pyrefly: ignore [missing-import]
from app.db.database import engine


PRICE_FILES = [
    (r"D:\projects\volatility-radar\database\processed\EURUSD_daily.csv", "EURUSD"),
    (r"D:\projects\volatility-radar\database\processed\GBPUSD_daily.csv", "GBPUSD"),
    (r"D:\projects\volatility-radar\database\processed\USDJPY_daily.csv", "USDJPY"),
]


def load_prices():

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE forex_prices"))

    for file_path, pair in PRICE_FILES:

        df = pd.read_csv(file_path)

        df["timestamp"] = pd.to_datetime(df["timestamp"])

        df = df.rename(columns={"timestamp": "date"})

        df["date"] = df["date"].dt.date

        df["pair"] = pair

        df = df[
            [
                "date",
                "pair",
                "open",
                "high",
                "low",
                "close",
            ]
        ]

        df.to_sql(
            "forex_prices",
            engine,
            if_exists="append",
            index=False,
            chunksize=1000,
        )

        print(f"{pair}: {len(df)} rows")


def load_calendar():

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE calendar_events"))

    df = pd.read_csv(r"D:\projects\volatility-radar\database\processed\economic_calendar_clean.csv")

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    print("Invalid dates:", df["date"].isna().sum())

    df = df.dropna(subset=["date"])

    df["date"] = df["date"].dt.date

    df = df[
        [
            "date",
            "time",
            "currency",
            "event",
            "impact",
            "actual",
            "previous"
        ]
    ]

    df.to_sql(
        "calendar_events",
        engine,
        if_exists="append",
        index=False,
        chunksize=1000,
    )

    print(f"Calendar: {len(df)} rows")


if __name__ == "__main__":

    load_prices()
    load_calendar()

    print("Load complete")