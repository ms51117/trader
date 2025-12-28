### core/strategy.py ###
import pandas as pd
import numpy as np
from core.indicators import ema, calculate_atr, supertrend


class DualSupertrendStrategy:
    def __init__(self, params):
        self.params = params

    def generate_signals(self, df):
        """
        استراتژی دوگانه سوپرترند (حالت Continuous/پیوسته)
        """
        df = df.copy()

        # 1. محاسبه اندیکاتورها
        # محاسبه ATR
        df['atr'] = calculate_atr(df, period=self.params['atr_period'])

        # محاسبه EMA 200
        df['ema_long'] = ema(df['close'], period=self.params['ema_period'])

        # محاسبه سوپرترند اصلی (Trend Filter)
        # فرض بر این است که تابع supertrend در indicators.py ستون روند را برمی‌گرداند یا به df اضافه می‌کند
        # در اینجا ما خروجی را گرفته و استفاده می‌کنیم
        st_main_dir = supertrend(
            df,
            period=self.params['st_period'],
            multiplier=self.params['st_multiplier']
        )
        # اگر خروجی سری باشد، نامگذاری میکنیم، اگر DF باشد فرض میکنیم ستون آخر است
        if isinstance(st_main_dir, pd.DataFrame):
            df['trend_main'] = st_main_dir.iloc[:, -1]  # فرض بر اینکه ستون آخر جهت روند است
        else:
            df['trend_main'] = st_main_dir

        # محاسبه سوپرترند سریع (Trigger)
        st_fast_dir = supertrend(
            df,
            period=self.params['st_fast_period'],
            multiplier=self.params['st_fast_multiplier']
        )
        if isinstance(st_fast_dir, pd.DataFrame):
            df['trend_fast'] = st_fast_dir.iloc[:, -1]
        else:
            df['trend_fast'] = st_fast_dir

        # 2. منطق ورود (پیوسته)
        # به جای بررسی لحظه کراس (که با shift انجام میشد)، وضعیت فعلی را چک می‌کنیم.

        # شرط ۱: سوپرترند اصلی صعودی باشد (معمولا ۱ برای صعود)
        cond_main = (df['trend_main'] == 1)

        # شرط ۲: سوپرترند سریع صعودی باشد
        cond_fast = (df['trend_fast'] == 1)

        # شرط ۳: قیمت بالای EMA 200 باشد
        cond_ema = (df['close'] > df['ema_long'])

        # ترکیب شرایط: تا زمانی که همه اینها برقرارند، سیگنال ورود فعال است
        buy_signal = cond_main & cond_fast & cond_ema

        # 3. خروجی
        df['signal'] = 0
        df.loc[buy_signal, 'signal'] = 1

        return df
