import os
os.chdir("D:/Projects/volatility-radar")

import numpy as np
import pandas as pd

df = pd.read_csv("data/processed_v2/merged.csv")

pair_map = {'EURUSD': 0, 'GBPUSD': 1, 'USDJPY': 2}
df['pair'] = df['pair'].map(pair_map)

df.to_csv("data/final_cleaned_data/full_features.csv", index=False)