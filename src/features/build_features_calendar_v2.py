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

        multiplier = 1.0
        if "<" in x:
            multiplier = 0.99
        elif ">" in x:
            multiplier = 1.01

        x = str(x).strip().upper()

        x = re.sub(r"[<>~]", "", x)

        if x == "" or x.lower() == 'nan':
            return np.nan

        if re.match(r'^\d+-\d+-\d+$', x):
            votes = [float(v) for v in x.split("-")]  # Convert to float immediately
            x = (votes[0] - votes[1]) / (votes[0] + votes[1] + votes[2])
            return x

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
            return convert(parts[0])

        return convert(x)

    df['actual_clean'] = df['actual'].apply(parse_value)
    df['previous_clean'] = df['previous'].apply(parse_value)

    df['change'] = df['actual_clean'] - df['previous_clean']

    df['change_rel'] = df['change'] / df['previous_clean'].abs()

    df['change_rel'] = df['change_rel'].replace([np.inf, -np.inf], 0)
    df['change_rel'] = df['change_rel'].fillna(0)

    df['z_score'] = df.groupby('event')['change_rel'].transform(lambda x: (x - x.mean()) / x.std())
    df['z_score'] = df['z_score'].fillna(0)

    impact_map = {'Low':1, 'Medium':2, 'High':3}
    df['impact_num'] = df['impact'].map(impact_map)

    df['signal'] = df['z_score'] * df['impact_num']

    return df

pairs = ['eurusd', 'gbpusd', 'usdjpy']

dfs = [build_calendar_features(i) for i in pairs]

calendar_features = pd.concat(dfs).reset_index(drop= True)
calendar_features.drop_duplicates().reset_index(drop = True)

calendar_features.to_csv('data/processed_v2/calendar_features.csv', index= False)
