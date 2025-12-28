# scripts/train_ai_model.py

import os
import sys
import joblib
import yaml
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

# اضافه کردن ریشه پروژه
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from core.indicators import (
    calculate_atr,
    calculate_rsi,
    calculate_adx
)

RAW_DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")
MODEL_DIR = os.path.join(ROOT_DIR, "outputs", "model_checkpoints")
ASSETS_FILE = os.path.join(ROOT_DIR, "config", "assets.yaml")


def load_assets():
    with open(ASSETS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["assets"]


def build_features(df):
    df = df.copy()

    df["returns"] = df["close"].pct_change()
    df["atr"] = calculate_atr(df)
    df["rsi"] = calculate_rsi(df["close"])
    df["adx"] = calculate_adx(df)

    df["atr_pct"] = df["atr"] / df["close"]
    df["return_std"] = df["returns"].rolling(20).std()
    df["volume_z"] = (
        (df["volume"] - df["volume"].rolling(20).mean()) /
        df["volume"].rolling(20).std()
    )

    # برچسب: حرکت سالم در 8 کندل آینده
    future_return = df["close"].shift(-8) / df["close"] - 1
    df["target"] = (future_return > 0.01).astype(int)

    features = df[[
        "atr_pct",
        "return_std",
        "rsi",
        "adx",
        "volume_z",
        "target"
    ]].dropna()

    return features


def load_all_data():
    assets = load_assets()
    dfs = []

    for asset in assets:
        symbol = asset["symbol"]
        timeframe = asset["timeframe"]

        file_path = os.path.join(
            RAW_DATA_DIR,
            f"{symbol}_{timeframe}.csv"
        )

        if not os.path.exists(file_path):
            print(f"❌ Missing data for {symbol}")
            continue

        df = pd.read_csv(file_path, parse_dates=["open_time"])
        df.set_index("open_time", inplace=True)

        features = build_features(df)
        dfs.append(features)

        print(f"{symbol}: {len(features)} rows")

    return pd.concat(dfs)


def train_model(dataset):
    X = dataset.drop("target", axis=1)
    y = dataset["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=True, random_state=42
    )

    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    print("\nModel Performance:")
    print(classification_report(y_test, preds))

    return model


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    dataset = load_all_data()
    print(f"\nTotal samples: {len(dataset)}")

    model = train_model(dataset)

    model_path = os.path.join(MODEL_DIR, "market_condition_xgb.pkl")
    joblib.dump(model, model_path)

    print(f"\n✅ Model saved at: {model_path}")


if __name__ == "__main__":
    main()
