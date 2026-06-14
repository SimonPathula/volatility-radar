import pandas as pd

pairs = ["EURUSD", "GBPUSD", "USDJPY"]

def concat_dfs(pair: str):
    df1 = pd.read_csv(f"D:/projects/volatility-radar/database/processed/{pair}_daily.csv")
    df1["timestamp"] = pd.to_datetime(df1["timestamp"]).dt.date
    df1 = df1.sort_values("timestamp", ascending= True)

    df2 = pd.read_csv(f"D:/projects/volatility-radar/database/raw/{pair}_daily.csv")
    df2["timestamp"] = pd.to_datetime(df2["timestamp"]).dt.date
    df2 = df2.sort_values("timestamp", ascending= True)

    df = pd.concat([df1, df2], ignore_index= True)

    return df

for pair in pairs:
    df = concat_dfs(pair)
    df.to_csv(f"D:/projects/volatility-radar/database/processed/{pair}_daily.csv", index=False)