# Automated Trading System

A Python-based automated trading system using multi-timeframe technical analysis, signal generation, and risk management. Supports backtesting on historical data and live signal generation with real-time prices.

---

## Features

- **Multi-timeframe analysis** — weekly, daily, 4-hour
- **12+ technical indicators** — MACD, RSI, ADX, ATR, Bollinger Bands, Stochastic, SMA, EMA
- **Signal generation** — buy/sell signals with 0–100% confidence scoring
- **Risk management** — automatic position sizing, daily loss limits, position limits
- **Portfolio tracking** — full P&L, open/closed positions, trade history
- **Backtesting** — trade-by-trade simulation with performance metrics
- **Real-time data** — live price patching via `fetch_realtime_data()`
- **Test suite** — 16 tests covering all documented examples

---

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `automated_trading_system.py` | Main orchestrator, data, backtesting | 585 |
| `trading_system.py` | Portfolio, positions, risk, order management | 571 |
| `signal_generator.py` | Technical analysis and signal generation | 486 |
| `backtest_framework.py` | Additional backtesting utilities | 437 |
| `test_examples.py` | 12 tests for QUICK_REFERENCE examples | 231 |
| `test_readme_examples.py` | 4 tests for README examples | 98 |
| `requirements.txt` | Python dependencies | — |
| `TRADING_SYSTEM_GUIDE.md` | Full documentation | — |
| `QUICK_REFERENCE.md` | Quick lookup guide | — |

---

## Quick Start

```bash
git clone https://github.com/edwinlau67/automated-trading-systems.git
cd automated-trading-systems
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

---

## Code Examples

### Example 1: Simple Backtest

```python
from automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="MSFT")
results = system.backtest("2023-01-01", "2024-01-31")

print(f"Return: {results['portfolio']['return_pct']:.2f}%")
print(f"Win Rate: {results['trades']['win_rate']:.2f}%")
print(f"Profit Factor: {results['trades']['profit_factor']:.2f}")
```

### Example 2: Real-Time Signal

```python
from automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(ticker="AAPL")
system.fetch_realtime_data(lookback_days=365)
system.calculate_indicators()

signal = system.generate_signals()
if signal:
    print(f"Signal: {signal}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"Entry: ${signal.entry_price:.2f}")
    print(f"Stop:  ${signal.stop_loss:.2f}")
    print(f"Target:${signal.take_profit:.2f}")
else:
    print("No signal (neutral conditions)")
```

### Example 3: Multi-Stock Comparison

```python
import pandas as pd
from automated_trading_system import AutomatedTradingSystem

results = {}
for ticker in ["AAPL", "MSFT", "GOOGL", "TSLA"]:
    system = AutomatedTradingSystem(10000, ticker)
    results[ticker] = system.backtest("2023-06-01", "2024-01-31")

df = pd.DataFrame({
    ticker: {
        'Return': r['portfolio']['return_pct'],
        'Win_Rate': r['trades']['win_rate'],
        'Profit_Factor': r['trades']['profit_factor']
    }
    for ticker, r in results.items()
}).T

print(df)
```

### Example 4: Custom Configuration

```python
from automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(
    initial_capital=50000,
    ticker="TSLA",
    max_positions=5,
    max_position_size_pct=0.10
)
system.risk_manager.max_daily_loss_pct = 0.03
results = system.backtest("2022-01-01", "2024-01-31")
system.print_detailed_results()
```

---

## Technical Indicators

| Category | Indicators |
|----------|-----------|
| Trend | SMA (20, 50, 200), EMA (12, 26) |
| Momentum | MACD, RSI, Stochastic Oscillator |
| Volatility | ATR, Bollinger Bands |
| Trend Strength | ADX, +DI, -DI |

---

## Signal Generation

Each signal is scored across five dimensions:

1. **Trend Alignment (25%)** — price vs. moving averages
2. **Momentum (25%)** — MACD, RSI, Stochastic
3. **Reversal (20%)** — divergences, support/resistance
4. **Volatility (15%)** — ADX trend strength
5. **Price Action (15%)** — higher highs/lows

Minimum confidence threshold: **55%**

---

## Performance Metrics

| Metric | Target |
|--------|--------|
| Return | > 0% |
| Win Rate | > 50% |
| Profit Factor | > 1.5 |
| Max Drawdown | < 20% |
| Sharpe Ratio | > 1.0 |

---

## Risk Management

- Automatic position sizing based on risk/reward
- Maximum concurrent positions
- Max % of portfolio per trade
- Daily loss limit — stops trading if threshold exceeded
- Stop loss and take profit enforcement

---

## Running Tests

```bash
python test_examples.py       # 12 tests
python test_readme_examples.py  # 4 tests
```

---

## Configuration

```python
system = AutomatedTradingSystem(
    initial_capital=10000,
    ticker="AAPL",
    max_positions=5,
    max_position_size_pct=0.05
)

system.risk_manager.max_daily_loss_pct = 0.02
system.risk_manager.max_positions = 10
system.portfolio.use_margin = False
```

---

## Disclaimer

This system is for educational and backtesting purposes only. Past performance does not guarantee future results. All trading involves risk of loss.
