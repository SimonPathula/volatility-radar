import numpy as np
import pandas as pd

#import the fully merged and cleaned dataset
df = pd.read_csv("D:/Projects/volatility-radar/data/processed/full_merged_clean.csv", delimiter= ",")

#First focus on the currency pairs and the price values
daily = df[['date', 'pair', 'open', 'high', 'low', 'close']].drop_duplicates(subset = ['date', 'pair'])

#sort the prices and date 
daily = daily.sort_values(['pair', 'date']).reset_index(drop = True)

#move the price columns one row above so we can predict the tomorrows result with current data
daily[['next_open', 'next_high', 'next_low', 'next_close']] = daily.groupby('pair')[['open', 'high', 'low', 'close']].shift(-1)

#find the return value from the next_day open and close values
daily['return'] = (daily['close'] - daily['open']) * 100/daily['open']

#now find the rolling standard deviation
daily['rolling_std'] = daily.groupby('pair')['return'].transform(
    lambda x : x.rolling(20, min_periods = 10).std()
)

# tomorrow's return — used only for label creation
daily['next_return'] = daily.groupby('pair')['close'].shift(-1) - daily.groupby('pair')['open'].shift(-1)

daily['next_return'] = daily['next_return'] / daily.groupby('pair')['open'].shift(-1) * 100

#now assign the labels with ±0.35σ, ±0.75σ and ±1.25σ
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

daily['label'] = daily.apply(assign_label, axis=1)

df = df.merge(daily[['date', 'pair', 'label', 
                      'rolling_std', 'return']], 
              on=['date', 'pair'], how='left')

df.dropna(subset=['label'], inplace=True)
df['label'] = df['label'].astype(int)

print(df.shape)
print(df['label'].value_counts().sort_index())

df.to_csv("data/processed/full_labeled.csv", index=False)
