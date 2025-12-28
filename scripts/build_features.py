import os
import glob
import pandas as pd
import numpy as np


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ساخت مسیرهای دقیق
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
FEATURE_DIR = os.path.join(PROJECT_ROOT, "data", "features")
FUTURE_BARS = 5      # حدود 20 ساعت روی 4H
ATR_PERIOD = 14


def calculate_atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr


def build_features(df):
    df = df.copy()

    # EMA
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["rsi"] = 100 - (100 / (1 + rs))

    # ATR
    df["atr"] = calculate_atr(df, ATR_PERIOD)

    # Trend strength
    df["trend_strength"] = (df["ema_50"] - df["ema_200"]) / df["atr"]

    return df


def build_label(df):
    df = df.copy()

    future_close = df["close"].shift(-FUTURE_BARS)
    move = (future_close - df["close"]) / df["atr"]

    df["label"] = (move > 1.0).astype(int)
    return df


def main():
    os.makedirs(FEATURE_DIR, exist_ok=True)
    all_assets = []

    for path in glob.glob(os.path.join(RAW_DIR, "*.csv")):
        asset = os.path.basename(path).split("_")[0]
        print(f"Processing {asset}")

        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df = build_features(df)
        df = build_label(df)

        df["asset"] = asset
        df.dropna(inplace=True)

        all_assets.append(df)

    final_df = pd.concat(all_assets)
    final_path = os.path.join(FEATURE_DIR, "ai_dataset.csv")
    final_df.to_csv(final_path)

    print(f"\n✅ Feature dataset saved: {final_path}")
    print(f"Rows: {len(final_df)}")


if __name__ == "__main__":
    main()
