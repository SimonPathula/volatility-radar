import os
os.chdir("D:/Projects/volatility-radar")

import pandas as pd
import numpy as np

price_df = pd.read_csv('data/processed_v2/pair_features.csv')
cal_df = pd.read_csv('data/processed_v2/calendar_features.csv')

currency_map = {
    'EUR': ['EURUSD'],
    'GBP': ['GBPUSD'],
    'JPY': ['USDJPY'],
    'USD': ['EURUSD', 'GBPUSD', 'USDJPY']
}

rows = []
for _, row in cal_df.iterrows():
    for pair in currency_map[row['currency']]:
        new_row = row.copy()
        new_row['pair'] = pair
        rows.append(new_row)

cal_expanded = pd.DataFrame(rows).reset_index(drop=True)

cal_agg = cal_expanded.groupby(['date', 'pair']).agg(
    high_impact_count=('impact_num', lambda x: (x == 3).sum()),
    medium_impact_count=('impact_num', lambda x: (x == 2).sum()),
    low_impact_count=('impact_num', lambda x: (x == 1).sum()),
    max_z_score=('z_score', lambda x: x.abs().max()),
    sum_signal=('signal', 'sum'),
    dominant_direction=('z_score', 'mean'),
    max_surprise_z=('surprise_z', lambda x: x.abs().max()),
    sum_signal_surprise=('signal_surprise', 'sum')
).reset_index()

df = price_df.merge(cal_agg, on=['date', 'pair'], how='left')

cal_cols = ['high_impact_count', 'medium_impact_count', 'low_impact_count',
            'max_z_score', 'sum_signal', 'dominant_direction',
            'max_surprise_z', 'sum_signal_surprise']

df[cal_cols] = df[cal_cols].fillna(0)

col = 'label'

df = df[[c for c in df.columns if c != col] + [col]]

df.to_csv("data/processed_v2/merged.csv", index= False)