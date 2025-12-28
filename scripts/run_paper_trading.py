### فایل scripts/run_paper_trading.py ###
import sys
import os
import time
import ccxt
import pandas as pd
import joblib
import numpy as np
from datetime import datetime

# افزودن مسیر ریشه پروژه
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.paper_account import PaperAccount
from core.strategy import DualSupertrendStrategy
from core.risk_manager import RiskManager
from core.indicators import calculate_rsi, calculate_adx, calculate_atr
from config import settings, assets

# --- تنظیمات ---
TIMEFRAME = "1h"  # تایم فریم لایو
LIMIT = 200  # تعداد کندل مورد نیاز برای محاسبات
CHECK_INTERVAL = 60  # هر چند ثانیه قیمت را چک کند (برای SL/TP)


def fetch_live_data(exchange, symbol, timeframe, limit):
    """دریافت آخرین کندل‌ها از صرافی"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index('time', inplace=True)
        return df
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return pd.DataFrame()


def prepare_ai_features(df):
    """آماده‌سازی داده برای هوش مصنوعی (مشابه فایل آموزش)"""
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

    # آخرین سطر که تمام ایندکس‌ها را دارد
    last_row = df.iloc[-1]

    # ساخت آرایه فیچرها دقیقا با ترتیب آموزش
    features = np.array([
        last_row["atr_pct"],
        last_row["return_std"],
        last_row["rsi"],
        last_row["adx"],
        last_row["volume_z"]
    ]).reshape(1, -1)

    # هندل کردن مقادیر NaN
    if np.isnan(features).any():
        return None

    return features


def run_live_bot():
    print("🚀 Starting Paper Trading Bot...")

    # 1. راه اندازی
    exchange = ccxt.binance()  # یا ccxt.kucoin()
    account = PaperAccount(initial_capital=1000)
    strategy = DualSupertrendStrategy(settings.STRATEGY_PARAMS)
    risk_manager = RiskManager(account.capital, risk_per_trade=0.01)

    # 2. لود کردن مدل هوش مصنوعی
    model_path = os.path.join("outputs", "model_checkpoints", "market_condition_xgb.pkl")
    if os.path.exists(model_path):
        ai_model = joblib.load(model_path)
        print("🧠 AI Model Loaded Successfully.")
    else:
        print("⚠️ AI Model not found! Running without AI.")
        ai_model = None

    asset_list = assets.load_assets()
    symbols = [a['symbol'] for a in asset_list]

    print(f"👀 Watching: {symbols}")
    print(f"💰 Current Capital: ${account.capital:.2f}")

    # حلقه بی نهایت
    while True:
        print(f"\n--- Scan: {datetime.now().strftime('%H:%M:%S')} ---")

        for symbol in symbols:
            # الف) دریافت قیمت لحظه‌ای برای مدیریت پوزیشن‌های باز
            try:
                ticker = exchange.fetch_ticker(symbol)
                current_price = ticker['last']

                # چک کردن حد سود و ضرر برای پوزیشن‌های باز
                if symbol in account.positions:
                    account.check_sl_tp(symbol, current_price)
                    continue  # اگر پوزیشن داریم، فعلا سیگنال جدید نمیگیریم (ساده سازی)
            except Exception as e:
                print(f"Network error on ticker {symbol}: {e}")
                continue

            # ب) تحلیل تکنیکال برای ورود جدید
            df = fetch_live_data(exchange, symbol, TIMEFRAME, LIMIT)
            if df.empty: continue

            # محاسبه سیگنال استراتژی
            # تابع generate_signal ما در core/strategy فقط آخرین کندل را برمیگرداند یا کل df؟
            # با توجه به کد قبلی، ما باید متد generate_signal را کمی تغییر میدادیم یا اینجا دستی حساب کنیم
            # اینجا برای اطمینان، اندیکاتورها را روی کل df میزنیم

            # 1. محاسبه اندیکاتورهای استراتژی
            df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
            # Supertrend محاسباتش پیچیده است، فرض بر این است که توابع در indicators.py درستند
            # اما چون supertrend روی کل دیتافریم کار میکند، اینجا مشکلی نیست

            # نکته: ما از کلاس strategy استفاده میکنیم که قبلا اصلاح کردیم تا generate_signals (جمع) داشته باشد
            # اما در فایل core/strategy.py شما متد generate_signal (مفرد) داشتید.
            # برای سادگی اینجا منطق را پیاده میکنیم یا باید فایل strategy را آپدیت کنید.
            # بیایید فرض کنیم فایل strategy.py را طبق دستورات قبلی آپدیت کردید.

            # فراخوانی استراتژی روی داده‌های جدید
            # ماژول strategy را ایمپورت کردیم. اگر متد generate_signals ندارد، دستی چک میکنیم:

            signal = strategy.generate_signal(df)  # فرض بر این است که این متد 0 یا 1 برمیگرداند برای کندل آخر

            if signal == 1:
                print(f"💡 Technical Signal detected for {symbol}")

                # ج) فیلتر هوش مصنوعی
                ai_approval = True
                if ai_model:
                    features = prepare_ai_features(df)
                    if features is not None:
                        prob = ai_model.predict_proba(features)[0][1]
                        if prob < 0.6:  # آستانه اطمینان
                            ai_approval = False
                            print(f"   ❌ AI Rejected (Prob: {prob:.2f})")
                        else:
                            print(f"   ✅ AI Approved (Prob: {prob:.2f})")
                    else:
                        print("   ⚠️ Not enough data for AI features")
                        ai_approval = False

                # د) ورود به معامله
                if ai_approval:
                    # محاسبه مدیریت ریسک
                    stop_loss = risk_manager.calculate_stop_loss(df, -1)  # -1 یعنی آخرین کندل
                    take_profit = risk_manager.calculate_take_profit(df, -1)

                    entry_price = current_price
                    pos_size = risk_manager.calculate_position_size(entry_price, stop_loss)

                    if pos_size > 0:
                        account.open_position(symbol, entry_price, pos_size, stop_loss, take_profit)

        # صبر تا سیکل بعدی
        print("Sleeping...", end="\r")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        run_live_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped manually.")
