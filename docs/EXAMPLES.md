# Code Examples

## 1. Simple Backtest

Run a backtest on AAPL with default settings.

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
results = system.backtest(start_date="2023-06-01", end_date="2024-01-31")
system.print_detailed_results()

print(f"Return: {results['portfolio']['return_pct']:.2f}%")
print(f"Win Rate: {results['trades']['win_rate']:.1f}%")
```

**Script:** `examples/01_simple_backtest.py`

---

## 2. Multi-Stock Comparison

Compare strategy performance across several tickers.

```python
import pandas as pd
from src.automated_trading_system import AutomatedTradingSystem

tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
results = {}

for ticker in tickers:
    system = AutomatedTradingSystem(10000, ticker)
    r = system.backtest("2023-01-01", "2024-01-01")
    results[ticker] = {
        "Return (%)": r["portfolio"]["return_pct"],
        "Win Rate (%)": r["trades"]["win_rate"],
        "Total Trades": r["trades"]["total_trades"],
    }

comparison = pd.DataFrame(results).T
print(comparison.to_string())
```

**Script:** `examples/02_multi_stock_comparison.py`

---

## 3. Custom Configuration

Override risk settings and indicator thresholds.

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(
    initial_capital=50000,
    ticker="TSLA",
    max_positions=3,
    max_position_size_pct=0.10,   # 10% per position
)

# Tighten daily loss limit
system.risk_manager.max_daily_loss_pct = 0.01

# Lower confidence threshold for more signals
system.signal_generator.confidence_threshold = 0.50

results = system.backtest("2023-01-01", "2024-01-01")
system.print_detailed_results()
```

**Script:** `examples/03_custom_configuration.py`

---

## 4. Real-Time Signal Generation

Fetch live data and generate today's trading signal.

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
ok = system.fetch_realtime_data(lookback_days=365)

if ok:
    system.calculate_indicators()
    signals = system.generate_signals()
    if signals:
        latest = signals[-1]
        print(f"Signal: {latest.signal_type}")
        print(f"Confidence: {latest.confidence:.1%}")
        print(f"Entry: ${latest.entry_price:.2f}")
        print(f"Stop: ${latest.stop_loss:.2f}")
        print(f"Target: ${latest.take_profit:.2f}")
        print(f"Reasons: {', '.join(latest.reason)}")
    else:
        print("No signal generated — conditions not met.")
```

**Script:** `examples/04_signal_generation.py`

---

## 5. Advanced Analysis with Report

Run backtest, generate charts, and save a Markdown report.

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=25000, ticker="NVDA")
system.backtest("2023-01-01", "2024-01-01")

report_path = system.save_report("2023-01-01", "2024-01-01")
print(f"Report saved to: {report_path}")
```

**Script:** `examples/05_advanced_analysis.py`

---

## Working with Indicators Directly

Use `IndicatorCalculator` as a standalone library.

```python
import yfinance as yf
from src.indicator_calculator import IndicatorCalculator

df = yf.download("SPY", start="2024-01-01", end="2024-12-31", progress=False)
if isinstance(df.columns, __import__("pandas").MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = IndicatorCalculator.calculate_all(df)

print(df[["Close", "SMA_20", "RSI", "MACD", "ADX"]].tail(5))
```

---

## Using Risk Profiles

Load a preset risk configuration from YAML.

```python
import yaml
from src.automated_trading_system import AutomatedTradingSystem

with open("config/risk_profiles.yml") as f:
    profiles = yaml.safe_load(f)

aggressive = profiles["aggressive"]

system = AutomatedTradingSystem(
    initial_capital=10000,
    ticker="AAPL",
    max_positions=aggressive["max_positions"],
    max_position_size_pct=aggressive["max_position_size_pct"],
)
system.risk_manager.max_daily_loss_pct = aggressive["max_daily_loss_pct"]
system.backtest("2023-01-01", "2024-01-01")
system.print_detailed_results()
```

---

## Accessing Portfolio After Backtest

Inspect positions and trade history programmatically.

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(10000, "MSFT")
system.backtest("2023-01-01", "2024-01-01")

summary = system.portfolio.get_portfolio_summary()
print(f"Final value: ${summary['total_value']:,.2f}")
print(f"Realized P&L: ${summary['realized_pnl']:,.2f}")

for trade in system.portfolio.closed_trades:
    pnl = (trade.exit_price - trade.entry_price) * trade.shares
    if trade.side == "SHORT":
        pnl = -pnl
    print(f"{trade.ticker} {trade.side}: ${pnl:+.2f}")
```
