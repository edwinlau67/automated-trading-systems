"""Test code examples from QUICK_REFERENCE.md"""
import sys
import traceback
import pandas as pd

PASS = "✓"
FAIL = "✗"
results = []

def run(label, fn):
    try:
        fn()
        print(f"{PASS} {label}")
        results.append((label, True, None))
    except Exception as e:
        print(f"{FAIL} {label}: {e}")
        results.append((label, False, traceback.format_exc()))

# -------------------------------------------------------------------
# 1. Import check
# -------------------------------------------------------------------
def test_import():
    from automated_trading_system import AutomatedTradingSystem
run("Import AutomatedTradingSystem", test_import)

# -------------------------------------------------------------------
# 2. Basic backtest
# -------------------------------------------------------------------
def test_backtest():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    results_data = system.backtest(start_date="2023-06-01", end_date="2024-01-31")
    assert results_data is not None, "backtest returned None"
    system.print_detailed_results()
run("Basic backtest (AAPL)", test_backtest)

# -------------------------------------------------------------------
# 3. Portfolio summary
# -------------------------------------------------------------------
def test_portfolio_summary():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.backtest(start_date="2023-06-01", end_date="2024-01-31")
    summary = system.portfolio.get_portfolio_summary()
    print(f"  Value: ${summary['total_value']:,.2f}")
    print(f"  Return: {summary['return_pct']:.2f}%")
    print(f"  Unrealized P&L: ${summary['unrealized_pnl']:,.2f}")
run("Portfolio summary", test_portfolio_summary)

# -------------------------------------------------------------------
# 4. Trade history
# -------------------------------------------------------------------
def test_trade_history():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.backtest(start_date="2023-06-01", end_date="2024-01-31")
    count = 0
    for trade in system.portfolio.closed_positions:
        print(f"  {trade.ticker}: {trade.side} | "
              f"Entry: ${trade.entry_price:.2f} | "
              f"Exit: ${trade.exit_price:.2f} | "
              f"P&L: ${trade.profit_loss:+.2f} ({trade.return_pct:+.2f}%)")
        count += 1
        if count >= 3:
            print("  ...")
            break
run("Trade history", test_trade_history)

# -------------------------------------------------------------------
# 5. Generate current signal
# -------------------------------------------------------------------
def test_generate_signal():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.fetch_data(start_date="2024-01-01", end_date="2024-06-30")
    system.calculate_indicators()
    signal = system.generate_signals()
    if signal:
        print(f"  Signal: {signal}")
        print(f"  Confidence: {signal.confidence:.1%}")
    else:
        print("  No signal generated (neutral market)")
run("Generate current signal", test_generate_signal)

# -------------------------------------------------------------------
# 6. Custom configuration backtest
# -------------------------------------------------------------------
def test_custom_config():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(
        initial_capital=50000,
        ticker="TSLA",
        max_positions=5,
        max_position_size_pct=0.10
    )
    system.risk_manager.max_daily_loss_pct = 0.03
    results_data = system.backtest("2023-01-01", "2024-01-31")
    assert results_data is not None
    print(f"  Return: {results_data['portfolio']['return_pct']:.2f}%")
run("Custom config backtest (TSLA)", test_custom_config)

# -------------------------------------------------------------------
# 7. Manual signal execution
# -------------------------------------------------------------------
def test_manual_signal():
    from automated_trading_system import AutomatedTradingSystem
    from signal_generator import Signal
    from datetime import datetime
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.fetch_data(start_date="2024-01-01", end_date="2024-06-30")
    signal = Signal(
        ticker="AAPL",
        timestamp=datetime.now(),
        signal_type="BUY",
        confidence=0.85,
        strength=30,
        entry_price=150.00,
        stop_loss=145.00,
        take_profit=160.00,
        reason=["Manual entry"]
    )
    system.execute_signal(signal)
    system.print_portfolio_status()
run("Manual signal execution", test_manual_signal)

# -------------------------------------------------------------------
# 8. Multi-stock comparison
# -------------------------------------------------------------------
def test_multi_stock():
    from automated_trading_system import AutomatedTradingSystem
    res = {}
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        system = AutomatedTradingSystem(initial_capital=10000, ticker=ticker)
        res[ticker] = system.backtest("2023-06-01", "2024-01-31")
    comparison = pd.DataFrame({
        ticker: {
            'Return': r['portfolio']['return_pct'],
            'Win_Rate': r['trades']['win_rate'],
            'Profit_Factor': r['trades']['profit_factor']
        }
        for ticker, r in res.items()
    }).T
    print(comparison.to_string())
run("Multi-stock comparison (AAPL/MSFT/GOOGL)", test_multi_stock)

# -------------------------------------------------------------------
# 9. Indicator values
# -------------------------------------------------------------------
def test_indicators():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.fetch_data(start_date="2024-01-01", end_date="2024-06-30")
    system.calculate_indicators()
    df = system.indicators['daily']
    latest = df.iloc[-1]
    print(f"  Price: ${latest['Close']:.2f}")
    print(f"  RSI: {latest['RSI']:.2f}")
    print(f"  MACD: {latest['MACD']:.4f}")
    print(f"  ADX: {latest['ADX']:.2f}")
    print(f"  ATR: ${latest['ATR']:.2f}")
run("Indicator values", test_indicators)

# -------------------------------------------------------------------
# 10. Signals history
# -------------------------------------------------------------------
def test_signals_history():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.backtest(start_date="2023-06-01", end_date="2024-01-31")
    print(f"  Total Signals: {len(system.signals_history)}")
    for i, sig in enumerate(system.signals_history[-3:], 1):
        print(f"  {i}. {sig}")
        print(f"     Confidence: {sig.confidence:.1%}")
        print(f"     Reasons: {', '.join(sig.reason)}")
run("Signals history", test_signals_history)

# -------------------------------------------------------------------
# 11. Realtime data fetch
# -------------------------------------------------------------------
def test_realtime_fetch():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    assert system.fetch_realtime_data(lookback_days=365), "fetch_realtime_data returned False"
    daily = system.data['daily']
    from datetime import datetime
    today = datetime.today().date()
    latest_date = daily.index[-1].date()
    assert latest_date == today, f"Latest bar {latest_date} is not today ({today})"
    print(f"  Latest bar: {latest_date}")
    print(f"  Close: ${daily['Close'].iloc[-1]:.2f}")
run("Realtime data fetch (today's bar)", test_realtime_fetch)

# -------------------------------------------------------------------
# 12. Realtime signal generation
# -------------------------------------------------------------------
def test_realtime_signal():
    from automated_trading_system import AutomatedTradingSystem
    system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
    system.fetch_realtime_data(lookback_days=365)
    system.calculate_indicators()
    df = system.indicators['daily']
    latest = df.iloc[-1]
    print(f"  Date:  {df.index[-1].date()}")
    print(f"  Close: ${latest['Close']:.2f}")
    print(f"  RSI:   {latest['RSI']:.2f}")
    print(f"  MACD:  {latest['MACD']:.4f}")
    print(f"  ADX:   {latest['ADX']:.2f}")
    signal = system.generate_signals()
    if signal:
        print(f"  Signal: {signal}")
        print(f"  Confidence: {signal.confidence:.1%}")
        print(f"  Entry: ${signal.entry_price:.2f} | Stop: ${signal.stop_loss:.2f} | Target: ${signal.take_profit:.2f}")
        print(f"  Reasons: {', '.join(signal.reason)}")
    else:
        print("  No signal (neutral conditions)")
run("Realtime signal generation (AAPL live)", test_realtime_signal)

# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
print("\n" + "="*50)
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
