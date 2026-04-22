# Automated Trading System - Quick Reference

## Installation & Setup (1 minute)

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from src.automated_trading_system import AutomatedTradingSystem; print('Ready')"
```

---

## Common Tasks

### Run Backtest
```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
results = system.backtest(start_date="2023-06-01", end_date="2024-01-31")
system.print_detailed_results()
```

### Get Portfolio Summary
```python
summary = system.portfolio.get_portfolio_summary()
print(f"Value: ${summary['total_value']:,.2f}")
print(f"Return: {summary['return_pct']:.2f}%")
print(f"Unrealized P&L: ${summary['unrealized_pnl']:,.2f}")
```

### View Trade History
```python
for trade in system.portfolio.closed_positions:
    print(f"{trade.ticker}: {trade.side} | "
          f"Entry: ${trade.entry_price:.2f} | "
          f"Exit: ${trade.exit_price:.2f} | "
          f"P&L: ${trade.profit_loss:+.2f} ({trade.return_pct:+.1f}%)")
```

### Generate Current Signal
```python
system.fetch_realtime_data(lookback_days=365)
system.calculate_indicators()
signal = system.generate_signals()  # returns Signal | None
if signal:
    system.display_latest_signal(signal)
    print(f"Confidence: {signal.confidence:.1%}")
```

### Custom Configuration
```python
system = AutomatedTradingSystem(
    initial_capital=50000,
    ticker="TSLA",
    max_positions=5,
    max_position_size_pct=0.10
)
system.risk_manager.max_daily_loss_pct = 0.03
results = system.backtest("2023-01-01", "2024-01-31")
```

### Execute Trade Manually
```python
from src.signal_generator import Signal
from datetime import datetime

signal = Signal(
    ticker="AAPL",
    timestamp=datetime.now(),
    signal_type="BUY",
    confidence=0.85,
    strength=30.0,
    entry_price=150.00,
    stop_loss=145.00,
    take_profit=160.00,
    reason=["Manual entry"]
)

system.execute_signal(signal)
system.print_portfolio_status()
```

### Compare Multiple Stocks
```python
import pandas as pd

results = {}
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    system = AutomatedTradingSystem(initial_capital=10000, ticker=ticker)
    results[ticker] = system.backtest("2023-06-01", "2024-01-31")

comparison = pd.DataFrame({
    ticker: {
        'Return': r['portfolio']['return_pct'],
        'Win_Rate': r['trades']['win_rate'],
        'Profit_Factor': r['trades']['profit_factor']
    }
    for ticker, r in results.items()
}).T

print(comparison)
```

### Analyze Indicator Values
```python
df = system.indicators['daily']
latest = df.iloc[-1]

print(f"Price: ${latest['Close']:.2f}")
print(f"RSI: {latest['RSI']:.2f}")
print(f"MACD: {latest['MACD']:.4f}")
print(f"ADX: {latest['ADX']:.2f}")
print(f"ATR: ${latest['ATR']:.2f}")
```

### View Signals Generated
```python
print(f"Total Signals: {len(system.signals_history)}")
print(f"\nLast 5 Signals:")
for i, signal in enumerate(system.signals_history[-5:], 1):
    print(f"  {i}. {signal}")
    print(f"     Confidence: {signal.confidence:.1%}")
    print(f"     Reasons: {', '.join(signal.reason)}")
```

### Save Charts and Report
```python
# Full report (charts + markdown) in runs/<TICKER>_<timestamp>/
run_folder = system.save_report("2023-01-01", "2024-01-01")
print(f"Report: {run_folder}/")

# Charts only
paths = system.save_charts()
```

### Export Trades to CSV
```python
csv_path = system.export_trades()
print(f"Exported to: {csv_path}")
```

---

## Configuration Parameters

### Risk Management
```python
system.risk_manager.max_positions = 5              # Max concurrent positions
system.risk_manager.max_position_size_pct = 0.05  # Max 5% per trade
system.risk_manager.max_daily_loss_pct = 0.02     # Stop if down 2%
system.risk_manager.max_correlation = 0.7         # Max correlation between positions
```

### Signal Generation
```python
system.signal_generator.confidence_threshold = 0.55  # Minimum signal confidence
```

### Portfolio (Margin)
```python
system.portfolio.margin_multiplier = 2.0   # 2x leverage (if use_margin=True)
system.portfolio.use_margin = True         # Enable margin trading
```

---

## Technical Indicators Reference

| Indicator | Purpose | Range | Signal |
|-----------|---------|-------|--------|
| **RSI** | Momentum | 0–100 | <30 oversold, >70 overbought |
| **MACD** | Trend | Unbounded | Histogram >0 bullish |
| **ADX** | Trend Strength | 0–100 | <15 no trend, >25 strong trend |
| **ATR** | Volatility | Unbounded | Higher = more volatile |
| **SMA 20/50/200** | Trend | Price | Price > SMA = uptrend |
| **EMA 12/26** | Trend | Price | EMA12 > EMA26 bullish |
| **Stochastic %K/%D** | Momentum | 0–100 | <20 oversold, >80 overbought |
| **Bollinger Bands** | Volatility | Price ±2σ | Squeeze = breakout expected |

---

## Signal Fields

| Field | Type | Description |
|-------|------|-------------|
| `signal_type` | str | `"BUY"` or `"SELL"` |
| `confidence` | float | 0.0–1.0 (≥0.55 required) |
| `entry_price` | float | Recommended entry |
| `stop_loss` | float | Risk limit |
| `take_profit` | float | Target price |
| `strength` | float | ADX value at signal time |
| `timeframe` | str | `"daily"`, `"weekly"`, `"4h"`, or `"multi"` |
| `reason` | list[str] | Indicators that triggered the signal |

---

## Performance Metrics

| Metric | Interpretation | Target |
|--------|----------------|--------|
| **Return** | Total portfolio gain/loss | >0% |
| **Win Rate** | % of winning trades | >50% |
| **Profit Factor** | Gross wins / gross losses | >1.5 |
| **Max Drawdown** | Largest peak-to-trough loss | <20% |
| **Avg Holding Days** | Average trade duration | Strategy-dependent |
| **Avg Win / Avg Loss** | Average dollar P&L | Avg win > Avg loss |

---

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| No signals | Check ADX > 15; run longer date range |
| Slow execution | Use shorter date range; data is cached after first fetch |
| No data | Verify ticker on Yahoo Finance |
| Capital errors | Reduce `max_position_size_pct` |
| Stale data | Call `system.clear_cache("AAPL")` and re-run |

---

## Data Sources

- **Yahoo Finance** (via yfinance): Free, no API key needed
- **Supported:** Stocks, ETFs, Indexes
- **Timeframes:** Daily, Weekly, 4-Hour (resampled from daily)
- **Cache:** `data/cache/<TICKER>_<start>_<end>.csv`

---

## File Structure

```
automated-trading-systems/
├── src/
│   ├── automated_trading_system.py  # Main orchestrator
│   ├── trading_system.py            # Portfolio, Risk, Orders
│   ├── signal_generator.py          # Signal generation
│   ├── indicator_calculator.py      # Technical indicators
│   ├── visualization.py             # Chart dashboards
│   ├── report.py                    # Markdown report
│   └── logger.py                    # Logging setup
├── config/                          # YAML configuration files
├── data/cache/                      # Downloaded price data (CSV)
├── data/backtest_results/           # Backtest JSON results
├── data/exports/                    # Trade export CSVs
├── examples/                        # Runnable example scripts
├── notebooks/                       # Jupyter analysis notebooks
├── runs/                            # Per-run chart + report folders
├── logs/                            # Rotating log files
└── requirements.txt
```

---

## Key Classes & Methods Summary

### AutomatedTradingSystem
```python
system = AutomatedTradingSystem(initial_capital, ticker, max_positions, max_position_size_pct)
system.fetch_data(start_date, end_date)
system.fetch_realtime_data(lookback_days=365)
system.calculate_indicators()
signal = system.generate_signals()          # returns Signal | None
system.execute_signal(signal)
system.backtest(start_date, end_date, signal_timeframe='daily')
system.print_detailed_results()
system.save_report(start_date, end_date)   # returns run folder path
system.save_charts()                        # returns list of PNG paths
system.export_trades()                      # returns CSV path
system.clear_cache(ticker=None)             # returns count removed
```

### PortfolioManager
```python
system.portfolio.open_position(ticker, entry_price, quantity, side, signal, stop_loss, take_profit)
system.portfolio.close_position(position_id, exit_price, exit_signal)
system.portfolio.update_position(position_id, current_price)
system.portfolio.get_portfolio_summary()
system.portfolio.closed_positions          # list of Trade objects
```

### RiskManager
```python
system.risk_manager.calculate_position_size(portfolio_value, risk_amount, stop_loss_distance)
system.risk_manager.validate_trade(portfolio, ticker, quantity, price, stop_loss)
system.risk_manager.can_open_position(portfolio, position_value)
system.risk_manager.check_daily_loss_limit(portfolio)
```

### SignalGenerator
```python
signal = system.signal_generator.generate_signal(df, row_idx, timeframe)
stats = system.signal_generator.get_signal_summary()
```

---

## Example: Complete Workflow

```python
from src.automated_trading_system import AutomatedTradingSystem

# 1. Initialize
system = AutomatedTradingSystem(
    initial_capital=10000,
    ticker="AAPL",
    max_positions=3
)

# 2. Backtest
results = system.backtest(
    start_date="2023-06-01",
    end_date="2024-01-31"
)

# 3. Analyze Results
print(f"Return: {results['portfolio']['return_pct']:.2f}%")
print(f"Win Rate: {results['trades']['win_rate']:.2f}%")
print(f"Total Trades: {results['trades']['total_trades']}")

# 4. View Details
system.print_detailed_results()

# 5. Save Report
run_folder = system.save_report("2023-06-01", "2024-01-31")

# 6. Iterate on Parameters
system2 = AutomatedTradingSystem(10000, "AAPL", max_positions=3)
system2.risk_manager.max_position_size_pct = 0.08
system2.backtest("2023-01-01", "2024-01-31")
```

---

## Important Notes

1. Backtest thoroughly before live trading
2. Use reasonable position sizes (2–5%)
3. Always use stop losses
4. Never trade with capital you cannot afford to lose
5. Past performance does not guarantee future results
6. Market conditions change — monitor and adapt

---

## Getting Help

1. Read error messages — they are descriptive
2. Check `docs/TRADING_SYSTEM_GUIDE.md` for the full guide
3. Check `docs/API_REFERENCE.md` for method signatures
4. Test with known tickers: AAPL, MSFT, GOOGL are reliable
5. Start simple — single stock, one year of data, then expand
