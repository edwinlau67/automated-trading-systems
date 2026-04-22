"""Example 5: Advanced Analysis — multi-timeframe confluence + full report."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.automated_trading_system import AutomatedTradingSystem
from src.signal_generator import MultiTimeframeSignalAnalyzer

TICKER     = "AAPL"
START_DATE = "2023-01-01"
END_DATE   = "2024-01-01"

# ── Backtest ───────────────────────────────────────────────────────────────
system = AutomatedTradingSystem(
    initial_capital=10000,
    ticker=TICKER,
    max_positions=5,
    max_position_size_pct=0.05,
)
results = system.backtest(start_date=START_DATE, end_date=END_DATE)

# ── Multi-timeframe confluence ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("MULTI-TIMEFRAME CONFLUENCE")
print("=" * 50)

mtf = MultiTimeframeSignalAnalyzer()
for timeframe in ["weekly", "daily", "4h"]:
    df = system.indicators.get(timeframe)
    if df is None or df.empty:
        print(f"  {timeframe:8s}: no data")
        continue
    latest = df.iloc[-1]
    rsi  = latest.get("RSI", float("nan"))
    adx  = latest.get("ADX", float("nan"))
    macd = latest.get("MACD", 0)
    sig  = latest.get("MACD_Signal", 0)
    bias = "Bullish" if macd > sig else "Bearish"
    print(f"  {timeframe:8s}: RSI={rsi:.1f}  ADX={adx:.1f}  MACD bias={bias}")

# ── Performance summary ────────────────────────────────────────────────────
p = results["portfolio"]
t = results["trades"]
print(f"\n{'='*50}")
print(f"PERFORMANCE SUMMARY")
print(f"{'='*50}")
print(f"  Return:        {p['return_pct']:+.2f}%")
print(f"  Win Rate:      {t['win_rate']:.1f}%")
print(f"  Profit Factor: {t['profit_factor']:.2f}")
print(f"  Trades:        {t['total_trades']}")

# ── Generate full report ───────────────────────────────────────────────────
run_path = system.save_report(start_date=START_DATE, end_date=END_DATE)
print(f"\nFull report: {run_path}/report.md")
