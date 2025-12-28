import pandas as pd
import numpy as np
from core.indicators import calculate_rsi, calculate_adx, calculate_atr


class BacktestEngine:
    def __init__(self, portfolio, strategy, risk_manager, ai_model=None):
        self.portfolio = portfolio
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.ai_model = ai_model

    def run(self, data_dict):
        results = {}
        for symbol, df in data_dict.items():
            # اطمینان از وجود داده کافی
            if len(df) < 200:
                print(f"Skipping {symbol}: Not enough data")
                continue

            print(f"Backtesting {symbol}...")

            # پیش‌محاسبه اندیکاتورهای استراتژی
            df = self.strategy.generate_signals(df)

            # پیش‌محاسبه اندیکاتورهای مورد نیاز AI (برای سرعت بیشتر)
            if self.ai_model:
                df = self._precalculate_ai_features(df)

            # حلقه روی کندل‌ها
            for i in range(200, len(df)):
                current_row = df.iloc[i]

                # مدیریت خروج (TP/SL)
                if symbol in self.portfolio.positions:
                    self._check_exits(symbol, current_row, i, df)

                # مدیریت ورود
                if current_row['signal'] == 1:
                    # اگر پوزیشن باز نداریم وارد شو
                    if symbol not in self.portfolio.positions:
                        can_enter = True

                        # اگر AI فعال است، از آن تاییدیه بگیر
                        if self.ai_model:
                            features = self._extract_features(df, i)
                            # مدل انتظار آرایه 2 بعدی دارد
                            features_array = features.values.reshape(1, -1)
                            # کلاس 1 یعنی سیگنال تایید است
                            prediction = self.ai_model.predict(features_array)[0]

                            if prediction == 0:
                                can_enter = False

                        if can_enter:
                            self._enter_trade(symbol, current_row, i, df)

            results[symbol] = df

        return results

    def _check_exits(self, symbol, current_row, idx, df):
        position = self.portfolio.positions[symbol]

        # چک کردن Stop Loss
        if current_row['low'] <= position['stop_loss']:
            exit_price = position['stop_loss']
            # شبیه‌سازی اسلیپیج در بدترین حالت (Open کندل بعدی شاید پایین‌تر باشد)
            # اما اینجا برای سادگی همان قیمت استاپ را می‌گیریم
            self.portfolio.close_position(symbol, exit_price, current_row.name, reason="SL")

        # چک کردن Take Profit
        elif current_row['high'] >= position['take_profit']:
            self.portfolio.close_position(symbol, position['take_profit'], current_row.name, reason="TP")

    def _enter_trade(self, symbol, current_row, idx, df):
        stop_loss = self.risk_manager.calculate_stop_loss(df, idx)

        # اگر استاپ لاس نامعتبر بود (مثلا بالاتر از قیمت فعلی برای خرید)
        if stop_loss >= current_row['close']:
            return

        position_size = self.risk_manager.calculate_position_size(
            current_row['close'], stop_loss
        )

        if position_size > 0:
            take_profit = self.risk_manager.calculate_take_profit(df, idx)
            self.portfolio.open_position(
                symbol, current_row['close'], position_size, stop_loss, take_profit, current_row.name
            )

    def _precalculate_ai_features(self, df):
        """محاسبه ستون‌های مورد نیاز AI قبل از شروع حلقه"""
        df = df.copy()
        # باید دقیقاً همان منطق train_ai_model باشد
        df["returns"] = df["close"].pct_change()
        # atr, rsi, adx قبلاً در استراتژی یا اینجا باید باشند
        # فرض می‌کنیم استراتژی ATR را حساب کرده، اگر نه:
        if 'atr' not in df.columns:
            df['atr'] = calculate_atr(df)

        df["rsi"] = calculate_rsi(df["close"])
        df["adx"] = calculate_adx(df)

        df["atr_pct"] = df["atr"] / df["close"]
        df["return_std"] = df["returns"].rolling(20).std()

        # Volume Z-Score
        vol_mean = df["volume"].rolling(20).mean()
        vol_std = df["volume"].rolling(20).std()
        df["volume_z"] = (df["volume"] - vol_mean) / (vol_std + 1e-9)  # جلوگیری از تقسیم بر صفر

        return df

    def _extract_features(self, df, i):
        """استخراج ویژگی‌های یک ردیف خاص برای پیش‌بینی"""
        # ترتیب ستون‌ها باید دقیقاً مثل زمان آموزش باشد
        feature_cols = ["atr_pct", "return_std", "rsi", "adx", "volume_z"]
        return df.iloc[i][feature_cols]
