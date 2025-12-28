### core/portfolio.py ###
import pandas as pd


class MultiAssetPortfolio:
    def __init__(self, initial_capital, assets_config):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.assets_config = assets_config
        self.positions = {}  # symbol -> position info
        self.trades = []
        # اضافه کردن لیست منحنی سرمایه برای محاسبه متریک‌ها
        self.equity_curve = [initial_capital]

    def allocate_capital(self, symbol):
        # تخصیص سرمایه بر اساس وزن هر ارز
        asset_config = next((a for a in self.assets_config if a['symbol'] == symbol), None)
        if asset_config:
            weight = asset_config.get('weight', 1.0 / len(self.assets_config))
        else:
            weight = 1.0 / len(self.assets_config)  # مقدار پیش‌فرض اگر پیدا نشد

        allocated = self.capital * weight
        return allocated

    def open_position(self, symbol, entry_price, position_size, stop_loss, take_profit, entry_time):
        allocated = self.allocate_capital(symbol)
        cost = position_size * entry_price

        # اگر سرمایه کافی نبود، سایز را تعدیل کن
        if cost > self.capital:
            position_size = self.capital / entry_price
            cost = self.capital  # تمام سرمایه باقی‌مانده

        self.positions[symbol] = {
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': entry_time
        }
        # کسر هزینه از سرمایه آزاد (در مارکت کریپتو اسپات، پول بلوکه می‌شود)
        self.capital -= cost

    def close_position(self, symbol, exit_price, exit_time, reason="Signal"):
        if symbol not in self.positions:
            return 0

        position = self.positions[symbol]
        # محاسبه مقدار بازگشتی (سایز * قیمت خروج)
        revenue = position['position_size'] * exit_price

        # محاسبه سود/ضرر خالص
        cost = position['position_size'] * position['entry_price']
        pnl = revenue - cost
        pnl_pct = (pnl / cost) * 100 if cost > 0 else 0

        # بازگشت سرمایه به حساب
        self.capital += revenue

        # ثبت ترید
        self.trades.append({
            'symbol': symbol,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'position_size': position['position_size'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': position['entry_time'],
            'exit_time': exit_time,
            'reason': reason
        })

        # به‌روزرسانی منحنی سرمایه (مهم برای رفع ارور)
        self.equity_curve.append(self.capital)

        del self.positions[symbol]
        return pnl
