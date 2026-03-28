import os
os.chdir("D:/Projects/volatility-radar")

import numpy as np
import pandas as pd

def build_currency_features(pair):

    df = pd.read_csv(f"data/processed/{pair}_daily_clean.csv")

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df['pair'] = pair

    col = 'pair'

    df  = df[[col] + [c for c in df.columns if c != col]]

    df['max_up_pips'] = round((df['high'] - df['open']) * 1e+04, 0).astype('int')
    df['max_down_pips'] = round((df['open'] - df['low']) * 1e+04, 0).astype('int')

    df['max_profit'] = (df['high'] - df['open']) * 100 / df['open']
    df['max_loss'] = (df['low'] - df['open']) * 100 / df['open']
    df['daily_return'] = (df['close'] - df['open']) * 100 / df['open']

    df['rolling_std'] = df['daily_return'].rolling(20, min_periods = 10).std()

    df = df.dropna(subset= ['rolling_std'])

    return df

pairs = ['EURUSD', 'GBPUSD', 'USDJPY']

dfs = [build_currency_features(i) for i in pairs]

pair_features = pd.concat(dfs).reset_index(drop = True)

pair_features.to_csv("data/processed_v2/pair_features.csv", index=False)

