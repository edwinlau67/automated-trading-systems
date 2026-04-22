# Automated Trading System - Quick Reference

## Installation & Setup (1 minute)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from automated_trading_system import AutomatedTradingSystem; print('✓ Ready')"
```

---

## Common Tasks

### ⚡ Run Backtest
```python
from automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
system.backtest(start_date="2023-06-01", end_date="2024-01-31")
system.print_detailed_results()
```

### 📊 Get Portfolio Summary
```python
summary = system.portfolio.get_portfolio_summary()
print(f"Value: ${summary['total_value']:,.2f}")
print(f"Return: {summary['return_pct']:.2f}%")
print(f"Unrealized P&L: ${summary['unrealized_pnl']:,.2f}")
```

### 📈 View Trade History
```python
for trade in system.portfolio.closed_positions:
    print(f"{trade.ticker}: {trade.side} | "
          f"Entry: ${trade.entry_price:.2f} | "
          f"Exit: ${trade.exit_price:.2f} | "
          f"P&L: ${trade.profit_loss:+.2f} ({trade.return_pct:+.2f}%)")
```

### 🎯 Generate Current Signal
```python
system.fetch_data(start_date="2024-01-01", end_date="2024-01-31")
system.calculate_indicators()
signal = system.generate_signals()
if signal:
    print(signal)
    print(f"Confidence: {signal.confidence:.1%}")
```

### ⚙️ Custom Configuration
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

### 💰 Execute Trade Manually
```python
from signal_generator import Signal
from datetime import datetime

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
```

### 📊 Compare Multiple Stocks
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

### 🔍 Analyze Indicator Values
```python
# Get latest indicator values
df = system.indicators['daily']
latest = df.iloc[-1]

print(f"Price: ${latest['Close']:.2f}")
print(f"RSI: {latest['RSI']:.2f}")
print(f"MACD: {latest['MACD']:.4f}")
print(f"ADX: {latest['ADX']:.2f}")
print(f"ATR: ${latest['ATR']:.2f}")
```

### 📋 View Signals Generated
```python
print(f"Total Signals: {len(system.signals_history)}")
print(f"\nLast 5 Signals:")
for i, signal in enumerate(system.signals_history[-5:], 1):
    print(f"  {i}. {signal}")
    print(f"     Confidence: {signal.confidence:.1%}")
    print(f"     Reasons: {', '.join(signal.reason)}")
```

---

## Configuration Parameters

### Risk Management
```python
system.risk_manager.max_positions = 10                # Max concurrent positions
system.risk_manager.max_position_size_pct = 0.05    # Max 5% per trade
system.risk_manager.max_daily_loss_pct = 0.02       # Stop if down 2%
system.risk_manager.max_correlation = 0.7           # Max correlation between positions
```

### Portfolio
```python
system.portfolio.margin_multiplier = 2.0            # 2x margin (if enabled)
system.portfolio.use_margin = True                  # Enable margin trading
```

### Data
```python
system.ticker = "AAPL"                              # Change stock ticker
# Supported timeframes: 'daily', 'weekly', '4h' (from fetch_data)
```

---

## Technical Indicators Reference

| Indicator | Purpose | Range | Signal |
|-----------|---------|-------|--------|
| **RSI** | Momentum | 0-100 | <30 oversold, >70 overbought |
| **MACD** | Trend | Unbounded | Histogram >0 bullish |
| **ADX** | Trend Strength | 0-100 | >25 strong trend |
| **ATR** | Volatility | Unbounded | Higher = more volatile |
| **SMA** | Trend | Price | Price >SMA = uptrend |
| **Stochastic** | Momentum | 0-100 | <20 oversold, >80 overbought |
| **Bollinger** | Volatility | Price ±2σ | Squeeze = breakout expected |

---

## Signal Components

Each signal includes:
- **signal_type**: "BUY" or "SELL"
- **confidence**: 0.0-1.0 (0.55+ required)
- **entry_price**: Recommended entry
- **stop_loss**: Risk limit
- **take_profit**: Target price
- **strength**: ADX value (trend strength)
- **reason**: List of indicators triggering signal

---

## Performance Metrics

| Metric | Interpretation | Target |
|--------|-----------------|--------|
| **Return** | Total portfolio gain/loss | >0% |
| **Win Rate** | % of winning trades | >50% |
| **Profit Factor** | Wins/Losses ratio | >1.5 |
| **Max Drawdown** | Largest loss from peak | <20% |
| **Sharpe Ratio** | Risk-adjusted return | >1.0 |
| **Avg Trade** | Average P&L per trade | >0 |

---

## Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| No signals | Check data quality, verify ADX > 15 |
| Slow execution | Use shorter date ranges for testing |
| Capital errors | Reduce max_position_size_pct |
| Invalid ticker | Verify on Yahoo Finance |
| Loss trades | Backtest longer periods, adjust indicators |

---

## Data Sources

- **Yahoo Finance** (via yfinance): Free, reliable, no API key needed
- **Supported**: Stocks, ETFs, Indexes
- **Timeframes**: Daily, Weekly, 4-Hour (derived from daily)
- **History**: Up to 100 years of data available

---

## File Structure

```
trading-system/
├── automated_trading_system.py    # Main orchestrator
├── trading_system.py              # Portfolio management
├── signal_generator.py            # Signal generation
├── backtest_framework.py          # Advanced backtesting
├── requirements.txt               # Dependencies
├── TRADING_SYSTEM_GUIDE.md       # Full documentation
└── QUICK_REFERENCE.md            # This file
```

---

## Key Classes & Methods

### AutomatedTradingSystem
```python
system = AutomatedTradingSystem(initial_capital, ticker, max_positions, max_position_size_pct)
system.fetch_data(start_date, end_date)
system.calculate_indicators()
system.generate_signals()
system.execute_signal(signal)
system.backtest(start_date, end_date, signal_timeframe)
system.print_detailed_results()
```

### PortfolioManager
```python
system.portfolio.open_position(ticker, entry_price, quantity, side, signal, stop_loss, take_profit)
system.portfolio.close_position(position_id, exit_price, exit_signal)
system.portfolio.update_position(position_id, current_price)
system.portfolio.get_portfolio_summary()
```

### RiskManager
```python
system.risk_manager.calculate_position_size(portfolio_value, risk_amount, stop_distance)
system.risk_manager.validate_trade(portfolio, ticker, quantity, price, stop_loss)
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
from automated_trading_system import AutomatedTradingSystem

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

# 5. Iterate on Parameters
system.risk_manager.max_position_size_pct = 0.08
system.backtest("2023-01-01", "2024-01-31")  # Try again
```

---

## Important Notes

⚠️ **Always Remember:**
1. Backtest thoroughly before live trading
2. Use reasonable position sizes (2-5%)
3. Always use stop losses
4. Never trade with capital you can't afford to lose
5. Past performance ≠ future results
6. Market conditions change - monitor and adapt

---

## Getting Help

1. **Read error messages** - Very descriptive
2. **Check TRADING_SYSTEM_GUIDE.md** - Comprehensive docs
3. **Test with known tickers** - AAPL, MSFT, GOOGL are reliable
4. **Verify data** - Check yfinance directly if unsure
5. **Start simple** - Single stock, 1 year data, then expand

---

Happy Trading! 🚀

For full documentation, see: `TRADING_SYSTEM_GUIDE.md`
