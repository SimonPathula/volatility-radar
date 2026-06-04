import os
import requests
import pandas as pd 
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

def fetch_forex_daily(from_symbol, to_symbol, start_date, end_date):

    url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}&interval=60min&outputsize=full&apikey={ALPHA_VANTAGE_KEY}&datatype=csv"

    r = requests.get(url)

    df = pd.read_csv(StringIO(r.text))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    df = df[(df.index >= start_date) & (df.index <= end_date)]

    print(f"{from_symbol}{to_symbol}: {df.shape}")

    df.to_csv(f"database/raw/{from_symbol}{to_symbol}_daily.csv")


fetch_forex_daily("EUR", "USD", "2026-03-13", "2026-06-02")
fetch_forex_daily("USD", "JPY", "2026-03-13", "2026-06-02")
fetch_forex_daily("GBP", "USD", "2026-03-13", "2026-06-02")
    