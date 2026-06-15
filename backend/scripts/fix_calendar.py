from sqlalchemy import text
from app.db.database import engine

with engine.begin() as conn:
    # Use ctid (PostgreSQL internal row id) instead of id column
    conn.execute(text("""
        DELETE FROM calendar_events
        WHERE ctid NOT IN (
            SELECT MIN(ctid)
            FROM calendar_events
            GROUP BY date, time, currency, event
        )
    """))
    print("Duplicates removed")

    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        uniq_cal_row
        ON calendar_events (date, time, currency, event)
    """))
    print("Unique index created")