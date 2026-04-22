"""Example 4: Real-Time Signal Generation — fetch live data and generate a signal."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(ticker="AAPL")
system.fetch_realtime_data(lookback_days=365)
system.calculate_indicators()

df = system.indicators["daily"]
latest = df.iloc[-1]

print(f"\nLatest bar: {df.index[-1].date()}")
print(f"  Close: ${latest['Close']:.2f}")
print(f"  RSI:   {latest['RSI']:.1f}")
print(f"  MACD:  {latest['MACD']:.4f} / Signal: {latest['MACD_Signal']:.4f}")
print(f"  ADX:   {latest['ADX']:.1f}")

signal = system.generate_signals()
print()
if signal:
    print(f"Signal:     {signal.signal_type}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"Entry:      ${signal.entry_price:.2f}")
    print(f"Stop:       ${signal.stop_loss:.2f}")
    print(f"Target:     ${signal.take_profit:.2f}")
    print(f"Reasons:")
    for r in signal.reason:
        print(f"  {r}")
else:
    print("No signal — neutral market conditions.")

summary = system.signal_generator.get_signal_summary()
print(f"\nSignal history: {summary['total_signals']} total "
      f"({summary['buy_signals']} buys, {summary['sell_signals']} sells)")
