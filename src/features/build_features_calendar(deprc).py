import os
os.chdir("D:/Projects/volatility-radar")

import re
import numpy as np
import pandas as pd

def build_calendar_features(pair):
    df = pd.read_csv(f"data/processed/{pair}_forex.csv")

    df['date'] = pd.to_datetime(df['date'])

    def convert(x):
        if pd.isna(x):
            return np.nan

        x = str(x).strip().upper()

        if x == "" or x.lower() == 'nan':
            return np.nan

        multiplier = 1.0
        if "<" in x:
            multiplier = 0.99
        elif ">" in x:
            multiplier = 1.01

        x = re.sub(r"[<>~]", "", x)

        try:
            if "%" in x:
                return float(x.replace("%", "")) / 100 * multiplier

            if "K" in x:
                return float(x.replace("K", "")) * 1e3 * multiplier

            if "M" in x:
                return float(x.replace("M", "")) * 1e6 * multiplier

            if "B" in x:
                return float(x.replace("B", "")) * 1e9 * multiplier

            if "T" in x:
                return float(x.replace("T", "")) * 1e12 * multiplier

            return float(x) * multiplier

        except:
            return np.nan

    def parse_value(x):
        if pd.isna(x):
            return [np.nan, np.nan]

        x = str(x).strip()

        if "|" in x:
            parts = [p.strip() for p in x.split('|')]
            return [convert(parts[0]), convert(parts[1])]

        return [convert(x), np.nan]

    df[['actual_1', 'actual_2']] = df['actual'].apply(parse_value).apply(pd.Series)
    df[['previous_1', 'previous_2']] = df['previous'].apply(parse_value).apply(pd.Series)

    

    return df




