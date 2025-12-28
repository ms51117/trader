### فایل core/paper_account.py ###
import json
import os
import pandas as pd
from datetime import datetime


class PaperAccount:
    def __init__(self, initial_capital=1000, state_file="paper_wallet.json"):
        self.state_file = state_file
        self.initial_capital = initial_capital

        # بارگذاری وضعیت قبلی یا ایجاد حساب جدید
        if os.path.exists(self.state_file):
            self.load_state()
        else:
            self.capital = initial_capital
            self.positions = {}  # {symbol: {entry_price, size, sl, tp}}
            self.history = []
            self.save_state()

    def save_state(self):
        data = {
            "capital": self.capital,
            "positions": self.positions,
            "history": self.history
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=4, default=str)

    def load_state(self):
        with open(self.state_file, "r") as f:
            data = json.load(f)
            self.capital = data["capital"]
            self.positions = data["positions"]
            self.history = data.get("history", [])

    def open_position(self, symbol, entry_price, size, sl, tp):
        if symbol in self.positions:
            print(f"⚠️ Position already open for {symbol}")
            return

        cost = size * entry_price
        if cost > self.capital:
            print(f"❌ Insufficient funds for {symbol}")
            return

        print(f"🟢 OPEN LONG: {symbol} @ {entry_price}")
        self.capital -= cost  # کسر از موجودی آزاد (مارجین)

        self.positions[symbol] = {
            "entry_price": entry_price,
            "size": size,
            "sl": sl,
            "tp": tp,
            "entry_time": datetime.now().isoformat()
        }
        self.save_state()

    def close_position(self, symbol, exit_price, reason):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        size = pos["size"]

        # محاسبه سود/ضرر
        pnl = (exit_price - pos["entry_price"]) * size
        revenue = (size * exit_price)  # بازگشت اصل پول + سود/ضرر

        self.capital += revenue

        trade_record = {
            "symbol": symbol,
            "entry": pos["entry_price"],
            "exit": exit_price,
            "pnl": pnl,
            "reason": reason,
            "time": datetime.now().isoformat()
        }
        self.history.append(trade_record)

        print(f"🔴 CLOSE {symbol}: {reason} | PnL: {pnl:.2f}$")

        del self.positions[symbol]
        self.save_state()

    def check_sl_tp(self, symbol, current_price):
        """بررسی می‌کند آیا قیمت به حد سود یا ضرر رسیده است"""
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]

        if current_price <= pos["sl"]:
            self.close_position(symbol, pos["sl"], "SL Hit")
        elif current_price >= pos["tp"]:
            self.close_position(symbol, pos["tp"], "TP Hit")
