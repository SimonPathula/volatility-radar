from sqlalchemy import text
from app.db.database import engine

with engine.begin() as conn:
    conn.execute(text("DELETE FROM model_validation_history"))
    conn.execute(text("DELETE FROM forex_prices"))
    conn.execute(text("DELETE FROM calendar_events"))
    print("All tables cleared")