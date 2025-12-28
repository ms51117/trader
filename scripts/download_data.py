# scripts/download_data.py

import os
import sys
import yaml
import pandas as pd
from datetime import datetime
from binance.client import Client

# اضافه کردن ریشه پروژه به path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from config import settings


DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")
ASSETS_FILE = os.path.join(ROOT_DIR, "config", "assets.yaml")


def load_assets():
    with open(ASSETS_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config["assets"]


def get_binance_client():
    # برای داده تاریخی API Key لازم نیست
    return Client()


def download_klines(symbol, interval, start_date):
    client = get_binance_client()

    klines = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_date
    )

    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume",
        "number_of_trades", "taker_buy_base_volume",
        "taker_buy_quote_volume", "ignore"
    ])

    df = df[[
        "open_time", "open", "high", "low", "close", "volume"
    ]]

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)

    df = df.astype(float)
    df.columns = ["open", "high", "low", "close", "volume"]

    return df


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    assets = load_assets()

    for asset in assets:
        symbol = asset["symbol"]
        timeframe = asset["timeframe"]
        start_date = asset["start_date"]

        print(f"Downloading {symbol} | {timeframe} | from {start_date}")

        df = download_klines(
            symbol=symbol,
            interval=timeframe.lower(),
            start_date=start_date
        )

        filename = f"{symbol}_{timeframe}.csv"
        filepath = os.path.join(DATA_DIR, filename)

        df.to_csv(filepath)
        print(f"Saved: {filepath} ({len(df)} rows)\n")


if __name__ == "__main__":
    main()
