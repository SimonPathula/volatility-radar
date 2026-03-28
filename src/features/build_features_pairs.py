import os
os.chdir("D:/Projects/volatility-radar")

import numpy as np
import pandas as pd

def build_currency_features(pair):

    df = pd.read_csv(f"data/processed/{pair}_daily_clean.csv")

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df = df.rename(columns= {'timestamp' : 'date'})

    df['pair'] = pair

    col = 'pair'

    df  = df[[col] + [c for c in df.columns if c != col]]

    df['max_up_pips'] = round((df['high'] - df['open']) * 1e+04, 0).astype('int')
    df['max_down_pips'] = round((df['open'] - df['low']) * 1e+04, 0).astype('int')

    df['max_profit'] = (df['high'] - df['open']) * 100 / df['open']
    df['max_loss'] = (df['low'] - df['open']) * 100 / df['open']
    df['daily_return'] = (df['close'] - df['open']) * 100 / df['open']

    df['rolling_std'] = df['daily_return'].rolling(20, min_periods = 10).std()


    df['next_return'] = df.groupby('pair')['close'].shift(-1) - df.groupby('pair')['open'].shift(-1)

    df['next_return'] = df['next_return'] / df.groupby('pair')['open'].shift(-1) * 100

    def assign_label(row):
        if pd.isna(row['next_return']) or pd.isna(row['rolling_std']):
            return np.nan
        
        move = row['next_return']
        
        t1 = 0.35 * row['rolling_std']  # medium threshold
        t2 = 0.75 * row['rolling_std']  # strong threshold
        t3 = 1.25 * row['rolling_std']  # very strong threshold
        
        if move > t3:
            return 6   # very strong up
        elif move > t2:
            return 5   # strong up
        elif move > t1:
            return 4   # medium up
        elif move < -t3:
            return 0   # very strong down
        elif move < -t2:
            return 1   # strong down
        elif move < -t1:
            return 2   # medium down
        else:
            return 3   # no move
    
    df['label'] = df.apply(assign_label, axis=1)

    df = df.dropna(subset= ['rolling_std', 'label'])
    df.drop(columns= ['next_return'], inplace= True)

    return df

pairs = ['EURUSD', 'GBPUSD', 'USDJPY']

dfs = [build_currency_features(i) for i in pairs]

pair_features = pd.concat(dfs).reset_index(drop = True)

pair_features.to_csv("data/processed_v2/pair_features.csv", index=False)

