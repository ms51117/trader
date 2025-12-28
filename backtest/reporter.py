### backtest/reporter.py ###
import pandas as pd


def generate_report(metrics, trades, output_path="outputs/final_report.txt"):
    lines = []
    lines.append("=" * 40)
    lines.append("        BACKTEST REPORT        ")
    lines.append("=" * 40)

    # بخش اطلاعات کلی
    lines.append(f"Period Start    : {metrics.get('Start Date', 'N/A')}")
    lines.append(f"Period End      : {metrics.get('End Date', 'N/A')}")
    lines.append(f"Duration        : {metrics.get('Duration', 'N/A')}")
    lines.append("-" * 40)

    # بخش مالی
    lines.append(f"Initial Capital : ${metrics.get('Initial Capital ($)', 0):,.2f}")
    lines.append(f"Final Capital   : ${metrics.get('Final Capital ($)', 0):,.2f}")
    lines.append(f"Net Profit      : ${metrics.get('Net Profit ($)', 0):,.2f}")
    lines.append("-" * 40)

    # بخش عملکرد
    lines.append(f"Total Return    : {metrics.get('Total Return (%)', 0):.2f}%")
    lines.append(f"Max Drawdown    : {metrics.get('Max Drawdown (%)', 0):.2f}%")
    lines.append(f"Win Rate        : {metrics.get('Win Rate (%)', 0):.2f}%")
    lines.append(f"Sharpe Ratio    : {metrics.get('Sharpe Ratio', 0):.2f}")
    lines.append(f"Total Trades    : {metrics.get('Total Trades', 0)}")
    lines.append("=" * 40)

    report_content = "\n".join(lines)

    # ذخیره در فایل
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # پرینت لیست تریدها در انتهای فایل (اختیاری)
        if trades:
            with open(output_path, "a", encoding="utf-8") as f:
                f.write("\n\n=== TRADES LIST ===\n")
                for t in trades:
                    f.write(str(t) + "\n")

    except Exception as e:
        print(f"Error saving report: {e}")

    # چاپ در ترمینال
    print("\n" + report_content + "\n")
    print(f"✅ Full report saved to {output_path}")
