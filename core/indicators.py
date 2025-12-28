### اصلاحیه کامل فایل core/indicators.py ###
import pandas as pd
import numpy as np


# =========================================
# Basic Indicators
# =========================================

def ema(series, period):
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_atr(df, period=14):
    """Average True Range"""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# Alias for compatibility
atr = calculate_atr


def calculate_rsi(series, period=14):
    """Relative Strength Index"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_adx(df, period=14):
    """Average Directional Index"""
    df = df.copy()
    alpha = 1 / period

    df['up_move'] = df['high'] - df['high'].shift(1)
    df['down_move'] = df['low'].shift(1) - df['low']

    df['pdm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
    df['ndm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)

    df['tr'] = calculate_atr(df, period=1)

    df['tr_s'] = df['tr'].ewm(alpha=alpha, adjust=False).mean()
    df['pdm_s'] = df['pdm'].ewm(alpha=alpha, adjust=False).mean()
    df['ndm_s'] = df['ndm'].ewm(alpha=alpha, adjust=False).mean()

    df['pdi'] = 100 * (df['pdm_s'] / df['tr_s'])
    df['ndi'] = 100 * (df['ndm_s'] / df['tr_s'])

    dx = 100 * abs(df['pdi'] - df['ndi']) / (df['pdi'] + df['ndi'])
    adx = dx.ewm(alpha=alpha, adjust=False).mean()

    return adx


# =========================================
# Complex Indicators
# =========================================

def supertrend(df, period=10, multiplier=3):
    """Supertrend Indicator (Optimized with NumPy)"""
    atr_val = calculate_atr(df, period).fillna(0)
    hl2 = (df["high"] + df["low"]) / 2

    # محاسبه باندهای اولیه
    upperband = hl2 + multiplier * atr_val
    lowerband = hl2 - multiplier * atr_val

    # تبدیل به آرایه نامپای برای سرعت و جلوگیری از وارنینگ
    close = df["close"].values
    upperband = upperband.values
    lowerband = lowerband.values

    final_upper = np.zeros(len(df))
    final_lower = np.zeros(len(df))
    trend = np.zeros(len(df))

    # مقداردهی اولیه
    final_upper[0] = upperband[0]
    final_lower[0] = lowerband[0]
    trend[0] = 1

    for i in range(1, len(df)):
        # محاسبه Final Upper Band
        if upperband[i] < final_upper[i - 1] or close[i - 1] > final_upper[i - 1]:
            final_upper[i] = upperband[i]
        else:
            final_upper[i] = final_upper[i - 1]

        # محاسبه Final Lower Band
        if lowerband[i] > final_lower[i - 1] or close[i - 1] < final_lower[i - 1]:
            final_lower[i] = lowerband[i]
        else:
            final_lower[i] = final_lower[i - 1]

        # تشخیص روند
        if trend[i - 1] == 1:
            if close[i] < final_lower[i - 1]:
                trend[i] = -1
            else:
                trend[i] = 1
        else:  # trend was -1
            if close[i] > final_upper[i - 1]:
                trend[i] = 1
            else:
                trend[i] = -1

    return pd.Series(trend, index=df.index)
