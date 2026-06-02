import re
import numpy as np
import pandas as pd

def build_price_features(df):

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df = df.rename(columns= {'timestamp' : 'date'})

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
        df[f'return_{n}d'] = df['close'].pct_change(n)

    df['rolling_std_5'] = df['daily_return'].rolling(5, min_periods = 3).std()
    df['rolling_std_10'] = df['daily_return'].rolling(10, min_periods = 5).std()
    df['rolling_std_20'] = df['daily_return'].rolling(20, min_periods = 10).std()

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

    df = df.dropna(subset= ['rsi_14', 'rolling_std_20'])

    return df

def build_calendar_features(df):
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

    impact_map = {'Low':1, 'Medium':2, 'High':3}
    df['impact_num'] = df['impact'].map(impact_map)

    return df

def create_calendar_signals(df):
    df['z_score'] = (
    df.groupby('event')['change_rel']
    .transform(lambda x: (x - x.mean()) / (x.std() + 1e-6))
    .fillna(0)
    )

    df['surprise_z'] = (
        df.groupby(['event', 'currency'])['change_rel']
        .transform(lambda x: (x - x.mean()) / (x.std() + 1e-6))
        .fillna(0)
    )

    df['signal'] = df['z_score'] * df['impact_num']
    df['signal_surprise'] = df['surprise_z'] * df['impact_num']

    df = df.drop_duplicates().reset_index(drop=True)

    return df

def aggregate_calendar_features(cal_df):

    cal_agg = cal_df.groupby(['date', 'pair']).agg(
        high_impact_count=('impact_num', lambda x: (x == 3).sum()),
        medium_impact_count=('impact_num', lambda x: (x == 2).sum()),
        low_impact_count=('impact_num', lambda x: (x == 1).sum()),
        max_z_score=('z_score', lambda x: x.abs().max()),
        sum_signal=('signal', 'sum'),
        dominant_direction=('z_score', 'mean'),
        max_surprise_z=('surprise_z', lambda x: x.abs().max()),
        sum_signal_surprise=('signal_surprise', 'sum')
    ).reset_index()

    return cal_agg

def merge_features(price_df, cal_df):
    cal_agg = aggregate_calendar_features(cal_df)

    df = price_df.merge(
        cal_agg,
        on=['date', 'pair'],
        how='left'
    )

    cal_cols = [
        'high_impact_count',
        'medium_impact_count',
        'low_impact_count',
        'max_z_score',
        'sum_signal',
        'dominant_direction',
        'max_surprise_z',
        'sum_signal_surprise'
    ]

    df[cal_cols] = df[cal_cols].fillna(0)

    return df

def generate_feature_vector(merge_df):
    