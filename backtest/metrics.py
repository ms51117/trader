### backtest/metrics.py ###
import numpy as np
import pandas as pd

def calculate_metrics(trades, equity_curve, initial_capital, start_date=None, end_date=None):
    """
    محاسبه شاخص‌های عملکرد با پشتیبانی از تاریخ و زمان
    """
    # مدیریت حالت بدون ترید یا داده ناقص
    if not trades or len(equity_curve) < 2:
        return {
            "Start Date": str(start_date) if start_date else "N/A",
            "End Date": str(end_date) if end_date else "N/A",
            "Duration": "N/A",
            "Initial Capital ($)": initial_capital,
            "Final Capital ($)": initial_capital,
            "Net Profit ($)": 0.0,
            "Total Return (%)": 0.0,
            "Max Drawdown (%)": 0.0,
            "Win Rate (%)": 0.0,
            "Sharpe Ratio": 0.0,
            "Total Trades": 0,
        }

    # 1. محاسبات سرمایه
    final_capital = equity_curve[-1]
    net_profit = final_capital - initial_capital
    total_return_pct = (net_profit / initial_capital) * 100

    # 2. محاسبات Drawdown
    peak = equity_curve[0]
    max_dd = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd

    # 3. آمار تریدها
    winning_trades = [t for t in trades if t["pnl"] > 0]
    win_rate = (len(winning_trades) / len(trades) * 100)

    # 4. نسبت شارپ (سالانه شده)
    returns = np.diff(equity_curve) / equity_curve[:-1]
    if len(returns) > 1 and np.std(returns) > 0:
        # فرض بر کندل‌های ساعتی (24 * 365)
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(24 * 365)
    else:
        sharpe = 0.0

    # 5. مدت زمان
    duration_str = "N/A"
    if start_date and end_date:
        try:
            duration_str = str(end_date - start_date).split('.')[0] # حذف میلی‌ثانیه
        except:
            pass

    return {
        "Start Date": str(start_date),
        "End Date": str(end_date),
        "Duration": duration_str,
        "Initial Capital ($)": round(initial_capital, 2),
        "Final Capital ($)": round(final_capital, 2),
        "Net Profit ($)": round(net_profit, 2),
        "Total Return (%)": round(total_return_pct, 2),
        "Max Drawdown (%)": round(max_dd * 100, 2),
        "Win Rate (%)": round(win_rate, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Total Trades": len(trades),
    }
