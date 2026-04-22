"""Example 1: Simple Backtest — run a single-ticker backtest and print results."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
results = system.backtest(start_date="2023-01-01", end_date="2024-01-01")

print(f"\nReturn:        {results['portfolio']['return_pct']:+.2f}%")
print(f"Win Rate:      {results['trades']['win_rate']:.1f}%")
print(f"Profit Factor: {results['trades']['profit_factor']:.2f}")
print(f"Total Trades:  {results['trades']['total_trades']}")

system.print_detailed_results()
