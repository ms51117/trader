### اصلاحیه کامل فایل core/risk_manager.py ###

class RiskManager:
    def __init__(self, initial_capital, risk_per_trade=0.01):
        self.capital = initial_capital
        self.risk_per_trade = risk_per_trade

    def calculate_position_size(self, entry_price, stop_loss_price):
        risk_amount = self.capital * self.risk_per_trade
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0:
            return 0
        position_size = risk_amount / risk_per_unit
        return position_size

    def calculate_stop_loss(self, df, current_idx, atr_multiplier=1.5):
        # استفاده از iloc برای دسترسی با ایندکس عددی
        # اگر ستون 'atr' وجود نداشت، مقدار پیش‌فرض یا محاسبه در لحظه نیاز است
        # فرض بر این است که engine.py ستون atr را ساخته است
        atr = df['atr'].iloc[current_idx]
        entry_price = df['close'].iloc[current_idx]

        stop_loss = entry_price - (atr * atr_multiplier)
        return stop_loss

    def calculate_take_profit(self, df, current_idx, atr_multiplier=3.0):
        atr = df['atr'].iloc[current_idx]
        entry_price = df['close'].iloc[current_idx]

        take_profit = entry_price + (atr * atr_multiplier)
        return take_profit
