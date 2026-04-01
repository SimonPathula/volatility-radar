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

    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
    df['is_month_start'] = df['date'].dt.is_month_start.astype(int)

    df['max_up_pips'] = round((df['high'] - df['open']) * 1e+04, 0).astype('int')
    df['max_down_pips'] = round((df['open'] - df['low']) * 1e+04, 0).astype('int')

    df['max_profit'] = (df['high'] - df['open']) * 100 / df['open']
    df['max_loss'] = (df['low'] - df['open']) * 100 / df['open']
    df['daily_return'] = (df['close'] - df['open']) * 100 / df['open']

    for n in [3, 5, 10]:
        df[f'return_{n}d'] = df.groupby('pair')['close'].pct_change(n)

    df['rolling_std_5'] = df['daily_return'].rolling(5, min_periods = 3).std()
    df['rolling_std_10'] = df['daily_return'].rolling(10, min_periods = 5).std()
    df['rolling_std_20'] = df['daily_return'].rolling(20, min_periods = 10).std()


    df['next_return'] = df.groupby('pair')['close'].shift(-1) - df.groupby('pair')['open'].shift(-1)

    df['next_return'] = df['next_return'] / df.groupby('pair')['open'].shift(-1) * 100

    def assign_label(row):
        if pd.isna(row['next_return']) or pd.isna(row['rolling_std_20']) or pd.isna(row['rolling_std_5']) or pd.isna(row['rolling_std_10']):
            return np.nan
        
        move = row['next_return']
        t1 = 0.35 * row['rolling_std_20']

        if move > t1:
            return 2   # bullish
        elif move < -t1:
            return 0   # bearish
        else:
            return 1   # neutral

    # def assign_label(row):
    #     if pd.isna(row['next_return']) or pd.isna(row['rolling_std_20']) or pd.isna(row['rolling_std_5']) or pd.isna(row['rolling_std_10']):
    #         return np.nan
        
    #     move = row['next_return']
        
    #     t1 = 0.35 * row['rolling_std_20']  # medium threshold
    #     t2 = 0.75 * row['rolling_std_20']  # strong threshold
    #     t3 = 1.25 * row['rolling_std_20']  # very strong threshold
        
    #     if move > t3:
    #         return 6   # very strong up
    #     elif move > t2:
    #         return 5   # strong up
    #     elif move > t1:
    #         return 4   # medium up
    #     elif move < -t3:
    #         return 0   # very strong down
    #     elif move < -t2:
    #         return 1   # strong down
    #     elif move < -t1:
    #         return 2   # medium down
    #     else:
    #         return 3   # no move
    
    df['label'] = df.apply(assign_label, axis=1)

    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))

    prev_close = df['close'].shift(1)
    hl = df['high'] - df['low']
    hc = (df['high'] - prev_close).abs()
    lc = (df['low'] - prev_close).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df['atr_14'] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

    df['momentum_5d'] = df['close'] - df['close'].shift(5)
    df['momentum_10d'] = df['close'] - df['close'].shift(10)

    df['dist_from_mean_20d'] = df['close'] - df['close'].rolling(20, min_periods=10).mean()

    df['daily_range'] = df['high'] - df['low']
    df['candle_body'] = (df['close'] - df['open']).abs()
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']

    df = df.dropna(subset= ['rsi_14', 'rolling_std_20', 'label'])
    df.drop(columns= ['next_return'], inplace= True)

    return df

pairs = ['EURUSD', 'GBPUSD', 'USDJPY']

dfs = [build_currency_features(i) for i in pairs]

pair_features = pd.concat(dfs).reset_index(drop = True)

pair_features.to_csv("data/processed_v2/pair_features.csv", index=False)

