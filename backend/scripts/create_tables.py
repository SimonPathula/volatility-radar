from sqlalchemy import text
from app.db.database import engine

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS forex_prices (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            pair VARCHAR(10) NOT NULL,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            CONSTRAINT uniq_pair_date UNIQUE (pair, date)
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id SERIAL PRIMARY KEY,
            date DATE,
            time VARCHAR(20),
            currency VARCHAR(10),
            event TEXT,
            impact VARCHAR(20),
            actual VARCHAR(50),
            previous VARCHAR(50),
            CONSTRAINT uniq_cal_row UNIQUE (date, time, currency, event)
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS model_validation_history (
            id SERIAL PRIMARY KEY,
            pair VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            prediction VARCHAR(10) NOT NULL,
            actual VARCHAR(10) NOT NULL,
            confidence FLOAT NOT NULL,
            top_drivers JSON,
            CONSTRAINT uniq_pair_date_val UNIQUE (pair, date)
        )
    """))
    print("All tables created successfully")