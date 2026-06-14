import pandas as pd
import calendar

def preprocess_calendar(df):
    parts = df['date'].str.split(' ', expand=True)

    month_map = {month: index for index, month in enumerate(calendar.month_abbr) if month}
    df['month_num'] = parts[1].map(month_map)
    df['day_num'] = parts[2].astype(int)

    year_change = ((df['month_num'] == 1) & (df['month_num'].shift(1) == 12)).cumsum()
    df['year'] = 2026 + year_change 

    df['date'] = pd.to_datetime(dict(year=df['year'], month=df['month_num'], day=df['day_num']))

    df.drop(columns=['month_num', 'day_num', 'year'], inplace=True)
    df.dropna(subset=["actual", "previous"], inplace= True)
    df['time'] = df['time'].ffill()
    df.drop(columns=['forecast'], inplace= True)

    return df

def concat_calendars(df1, df2):

    df2 = preprocess_calendar(df2)

    df1["date"] = pd.to_datetime(df1["date"]).dt.date
    df2["date"] = pd.to_datetime(df2["date"]).dt.date

    df = pd.concat([df1, df2], ignore_index= True)
    df = df.drop_duplicates()

    return df

df1 = pd.read_csv("D:/projects/volatility-radar/database/processed/economic_calendar_clean.csv")

df2 = pd.read_csv("D:/projects/volatility-radar/database/raw/economic_calendar_raw.csv")

df = concat_calendars(df1, df2)
df.to_csv("D:/projects/volatility-radar/database/processed/economic_calendar_clean.csv", index=False)
