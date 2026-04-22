"""Example 2: Multi-Stock Comparison — backtest several tickers and compare."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.automated_trading_system import AutomatedTradingSystem

TICKERS     = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
START_DATE  = "2023-01-01"
END_DATE    = "2024-01-01"

rows = {}
for ticker in TICKERS:
    system = AutomatedTradingSystem(initial_capital=10000, ticker=ticker)
    r = system.backtest(start_date=START_DATE, end_date=END_DATE)
    rows[ticker] = {
        "Return (%)":     round(r["portfolio"]["return_pct"], 2),
        "Win Rate (%)":   round(r["trades"]["win_rate"], 1),
        "Profit Factor":  round(r["trades"]["profit_factor"], 2),
        "Total Trades":   r["trades"]["total_trades"],
        "Max Drawdown (%)": round(r["portfolio"].get("max_drawdown", 0), 2),
    }

df = pd.DataFrame(rows).T
df = df.sort_values("Return (%)", ascending=False)

print("\n" + "=" * 60)
print("MULTI-STOCK COMPARISON")
print("=" * 60)
print(df.to_string())
