### scripts/run_backtest.py ###
import sys
import os
from pathlib import Path
import pandas as pd
import joblib

# اضافه کردن مسیر پروژه به sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from config.assets import load_assets
from core.strategy import DualSupertrendStrategy
from core.risk_manager import RiskManager
from core.portfolio import MultiAssetPortfolio
from backtest.engine import BacktestEngine
from backtest.metrics import calculate_metrics
from backtest.reporter import generate_report


def main():
    print("🚀 Starting Professional Backtest...\n")

    # 1. Load Data
    print("📥 Loading Data...")
    assets_config = load_assets()
    data_dict = {}
    all_dates = []

    for asset in assets_config:
        symbol = asset['symbol']
        timeframe = asset['timeframe']
        file_path = Path(settings.DATA_DIR) / "raw" / f"{symbol}_{timeframe}.csv"

        if file_path.exists():
            df = pd.read_csv(file_path)
            if 'open_time' in df.columns:
                df['open_time'] = pd.to_datetime(df['open_time'])
                df.set_index('open_time', inplace=True)

                data_dict[symbol] = df
                all_dates.extend(df.index.tolist())
                print(f"   ✅ {symbol}: {len(df)} candles loaded.")
            else:
                print(f"   ⚠️ Date column missing in {symbol}")
        else:
            print(f"   ❌ File not found: {file_path}")

    if not data_dict:
        print("⛔ No data loaded. Exiting.")
        return

    # محاسبه بازه زمانی
    start_date = min(all_dates) if all_dates else None
    end_date = max(all_dates) if all_dates else None

    # 2. Setup Components
    print("\n⚙️ Setting up Strategy & Risk Manager...")

    # لود مدل AI (در صورت وجود)
    ai_model = None
    model_path = Path(settings.MODEL_DIR) / "market_condition_xgb.pkl"
    if model_path.exists():
        try:
            ai_model = joblib.load(model_path)
            print(f"   🧠 AI Model loaded successfully.")
        except Exception as e:
            print(f"   ⚠️ AI Model load failed: {e}")

    strategy = DualSupertrendStrategy(settings.STRATEGY_PARAMS)

    risk_manager = RiskManager(
        initial_capital=settings.INITIAL_CAPITAL,
        risk_per_trade=settings.RISK_PER_TRADE
    )

    # === FIX: پاس دادن assets_config برای رفع خطا ===
    portfolio = MultiAssetPortfolio(
        initial_capital=settings.INITIAL_CAPITAL,
        assets_config=assets_config
    )

    # 3. Run Backtest
    print("\n▶️ Running Backtest Engine...")
    engine = BacktestEngine(portfolio, strategy, risk_manager, ai_model=ai_model)
    engine.run(data_dict)

    # 4. Calculate Metrics & Report
    print("\n📊 Calculating Performance Metrics...")

    metrics = calculate_metrics(
        portfolio.trades,
        portfolio.equity_curve,
        settings.INITIAL_CAPITAL,
        start_date=start_date,
        end_date=end_date
    )

    # نمایش در کنسول
    print(f"\n======== RESULTS ========")
    print(f"💰 Final Capital: ${metrics['Final Capital ($)']}")
    print(f"📈 Total Return:  {metrics['Total Return (%)']}%")
    print(f"📉 Max Drawdown:  {metrics['Max Drawdown (%)']}%")
    print(f"✅ Win Rate:      {metrics['Win Rate (%)']}%")
    print(f"🔢 Total Trades:  {metrics['Total Trades']}")
    print(f"=========================")

    # ذخیره گزارش
    output_file = Path(settings.OUTPUT_DIR) / "backtest_report.txt"
    generate_report(metrics, portfolio.trades, output_path=str(output_file))


if __name__ == "__main__":
    main()
