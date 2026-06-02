import pandas as pd
# pyrefly: ignore [missing-import]
from app.db.database import engine

print(pd.read_sql("SELECT COUNT(*) cnt FROM forex_prices", engine))
print(pd.read_sql("SELECT COUNT(*) cnt FROM calendar_events", engine))