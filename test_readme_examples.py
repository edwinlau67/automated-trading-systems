"""Test code examples from README.md"""
import sys
import traceback
import pandas as pd
from automated_trading_system import AutomatedTradingSystem

PASS = "✓"
FAIL = "✗"
results = []

def run(label, fn):
    try:
        fn()
        print(f"{PASS} {label}\n")
        results.append((label, True, None))
    except Exception as e:
        print(f"{FAIL} {label}: {e}\n")
        results.append((label, False, traceback.format_exc()))


# Example 1: Simple Backtest
def example_1():
    system = AutomatedTradingSystem(initial_capital=10000, ticker="MSFT")
    results_data = system.backtest("2023-01-01", "2024-01-31")
    print(f"Return: {results_data['portfolio']['return_pct']:.2f}%")
    print(f"Win Rate: {results_data['trades']['win_rate']:.2f}%")
    print(f"Profit Factor: {results_data['trades']['profit_factor']:.2f}")

run("Example 1: Simple Backtest (MSFT)", example_1)


# Example 2: Multi-Stock Comparison
def example_2():
    res = {}
    for ticker in ["AAPL", "MSFT", "GOOGL", "TSLA"]:
        system = AutomatedTradingSystem(10000, ticker)
        res[ticker] = system.backtest("2023-06-01", "2024-01-31")

    df = pd.DataFrame({
        ticker: {
            'Return': r['portfolio']['return_pct'],
            'Win_Rate': r['trades']['win_rate'],
            'Profit_Factor': r['trades']['profit_factor']
        }
        for ticker, r in res.items()
    }).T
    print(df.to_string())

run("Example 2: Multi-Stock Comparison (AAPL/MSFT/GOOGL/TSLA)", example_2)


# Example 3: Custom Configuration
def example_3():
    system = AutomatedTradingSystem(
        initial_capital=50000,
        ticker="TSLA",
        max_positions=5,
        max_position_size_pct=0.10
    )
    system.risk_manager.max_daily_loss_pct = 0.03
    results_data = system.backtest("2022-01-01", "2024-01-31")
    system.print_detailed_results()

run("Example 3: Custom Configuration (TSLA 2-year)", example_3)


# Example 4: Generate Real-Time Signal
def example_4():
    system = AutomatedTradingSystem(ticker="AAPL")
    system.fetch_data("2024-01-01", "2024-06-30")
    system.calculate_indicators()
    signal = system.generate_signals()
    if signal:
        print(f"Signal: {signal}")
        print(f"Confidence: {signal.confidence:.1%}")
        print(f"Entry: ${signal.entry_price:.2f}")
        print(f"Stop: ${signal.stop_loss:.2f}")
        print(f"Target: ${signal.take_profit:.2f}")
        system.execute_signal(signal)
    else:
        print("No signal generated (neutral conditions)")

run("Example 4: Real-Time Signal (AAPL)", example_4)


# Summary
print("=" * 50)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")

if failed:
    print("\nFailure details:")
    for label, ok, tb in results:
        if not ok:
            print(f"\n--- {label} ---")
            print(tb)
    sys.exit(1)
