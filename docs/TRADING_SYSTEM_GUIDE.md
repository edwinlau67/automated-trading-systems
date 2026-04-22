# Automated Trading System - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [System Components](#system-components)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This is a **production-ready automated trading system** that:
- Analyzes multiple timeframes (weekly, daily, 4-hour)
- Generates algorithmic trading signals with confidence scoring
- Manages positions and risk automatically
- Tracks performance and generates charts and Markdown reports
- Backtests strategies on historical data with results cached to disk

**Key Features:**
- Multi-indicator technical analysis (19 indicator columns)
- Multi-timeframe signal consensus (requires ≥2 timeframes to agree)
- Automatic position sizing based on risk management
- Complete portfolio tracking and P&L analysis
- Structured logging to file and console
- Easy configuration for different trading styles

---

## Architecture

```
  ┌───────────────────────────────────────────────────────────────────────┐
  │                       User / Examples / Notebooks                     │
  └───────────────────────────────────────────────────────────────────────┘
                                        │
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ❶  DATA LAYER                                                        ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  yfinance.download()  ──►  CSV cache (data/cache/)                    ║
  ║  Resample  ──►  daily  ·  weekly  ·  4h  DataFrames                   ║
  ╚═══════════════════════════════╦═══════════════════════════════════════╝
                                  ║
                                  ▼
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ❷  INDICATOR CALCULATION LAYER                                       ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  SMA 20/50/200  ·  EMA 12/26  ·  MACD  ·  RSI  ·  RSI Divergence      ║
  ║  ATR  ·  ADX  ·  Bollinger Bands  ·  Stochastic %K/%D   [19 cols]     ║
  ╚═══════════════════════════════╦═══════════════════════════════════════╝
                                  ║
                                  ▼
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ❸  SIGNAL GENERATION LAYER                                           ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  5-component scoring model  (confidence threshold  0.55)              ║
  ║  ┌──────────────────┬───────┬─────────────────────────────────────┐   ║
  ║  │ Trend Alignment  │  25%  │ SMA 20/50  ·  EMA 12/26             │   ║
  ║  │ Momentum         │  25%  │ MACD  ·  RSI  ·  Stochastic         │   ║
  ║  │ Reversal         │  20%  │ RSI divergence  ·  Bollinger        │   ║
  ║  │ Volatility / ADX │  15%  │ ADX  (suppressed if ADX < 15)       │   ║
  ║  │ Price Action     │  15%  │ Higher / lower highs and lows       │   ║
  ║  └──────────────────┴───────┴─────────────────────────────────────┘   ║
  ║  Multi-Timeframe: weekly  ·  daily  ·  4h  →  consensus (≥ 2 agree)   ║
  ╚═══════════════════════════════╦═══════════════════════════════════════╝
                                  ║
                                  ▼
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ❹  RISK MANAGEMENT LAYER                                             ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  ✓ Position count limit   ✓ Position size limit                       ║
  ║  ✓ Daily loss limit       ✓ Capital availability                      ║
  ╚═══════════════════════════════╦═══════════════════════════════════════╝
                                  ║
                                  ▼
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ❺  EXECUTION LAYER                                                   ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  OrderManager.place_order / execute_order                             ║
  ║  PortfolioManager.open_position / close_position                      ║
  ║  Stop-loss  ·  Take-profit monitoring per bar                         ║
  ╚═══════════════════════════════╦═══════════════════════════════════════╝
                                  ║
                                  ▼
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║  ❻  REPORTING LAYER                                                   ║
  ╠═══════════════════════════════════════════════════════════════════════╣
  ║  visualization.py  ──►  4 chart dashboards (PNG)                      ║
  ║  report.py         ──►  runs/<TICKER>_<ts>/report.md                  ║
  ║  data/backtest_results/*.json  ·  data/exports/*.csv                  ║
  ╚═══════════════════════════════════════════════════════════════════════╝
```

---

## Installation

### 1. Install Python 3.8+
```bash
python --version
```

### 2. Clone or Download the Repository
```bash
git clone <repo-url>
cd automated-trading-systems
```

### 3. Create Virtual Environment and Install Dependencies
```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "import pandas; import numpy; import yfinance; print('All dependencies installed')"
python -c "from src.automated_trading_system import AutomatedTradingSystem; print('System ready')"
```

---

## Quick Start

### Run a Complete Backtest in 3 Lines
```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
system.backtest(start_date="2023-06-01", end_date="2024-01-31")
system.print_detailed_results()
```

### Example Output:
```
======================================================================
BACKTESTING
======================================================================
INFO      Fetching data  ticker=AAPL  2023-06-01 -> 2024-01-31
INFO      Data fetched  bars=160  range=2023-06-01 -> 2024-01-31
INFO      Indicators ready  timeframes=['daily', 'weekly', '4h']

INFO      Trade opened  AAPL  LONG  shares=8.42  entry=$72.50 ...
INFO      Position closed  AAPL  LONG  LOSS  exit=$69.37  pnl=$-26.30

======================================================================
TRADING SYSTEM SUMMARY
======================================================================

PORTFOLIO:
  Initial Capital:    $10,000.00
  Total Value:         $9,973.70
  Cash:                $9,973.70
  Return:                 -0.26%
  Unrealized P&L:          $0.00
  Realized P&L:           -$26.30

TRADES:
  Total Trades:               1
  Winning Trades:             0
  Losing Trades:              1
  Win Rate:               0.00%
  Profit Factor:           0.00
```

---

## System Components

### 1. **AutomatedTradingSystem** — Orchestrator (`src/automated_trading_system.py`)

Coordinates all components and manages the trading workflow.

**Key Methods:**
```python
# Data
system.fetch_data(start_date, end_date)
system.fetch_realtime_data(lookback_days=365)

# Indicators
system.calculate_indicators()

# Signals
signal = system.generate_signals()          # returns Signal | None
system.display_latest_signal(signal)

# Execution
system.execute_signal(signal)
system.check_exit_conditions(current_price)
system.close_position(reason, exit_price)

# Backtesting
results = system.backtest(start_date, end_date, signal_timeframe='daily')
system.print_detailed_results()

# Reporting & Export
run_folder = system.save_report(start_date, end_date)
paths = system.save_charts()
csv_path = system.export_trades()
removed = system.clear_cache(ticker=None)
```

### 2. **PortfolioManager** — Position & Capital Management (`src/trading_system.py`)

Manages open positions, cash, and portfolio equity.

**Key Methods:**
```python
position = portfolio.open_position(ticker, entry_price, quantity, side,
                                   signal, stop_loss, take_profit)
trade = portfolio.close_position(position_id, exit_price, exit_signal)
portfolio.update_position(position_id, current_price)
summary = portfolio.get_portfolio_summary()
snapshot = portfolio.create_snapshot()
```

**Key Attributes:**
- `portfolio.closed_positions` — list of completed `Trade` objects
- `portfolio.positions` — dict of open `Position` objects keyed by position_id
- `portfolio.total_value` — current portfolio value
- `portfolio.cash` — available cash

### 3. **SignalGenerator** — Technical Analysis (`src/signal_generator.py`)

Analyzes technical indicators and generates trading signals per bar.

**Signal Scoring Model (5 components):**
- **Trend Alignment (25%):** Price vs SMA20/50, EMA12 vs EMA26
- **Momentum (25%):** MACD, RSI, Stochastic
- **Reversal (20%):** RSI divergence, Bollinger Band extremes
- **Volatility/ADX (15%):** ADX strength; signal suppressed if ADX < 15
- **Price Action (15%):** Higher highs/lows (BUY) or lower highs/lows (SELL)

**Confidence Threshold:** ≥0.55 to emit a signal

```python
signal = system.signal_generator.generate_signal(df, row_idx, timeframe)
stats = system.signal_generator.get_signal_summary()
```

### 4. **MultiTimeframeSignalAnalyzer** — Confluence (`src/signal_generator.py`)

Combines per-timeframe signals into a single consensus signal.

- Requires at least 2 timeframes to emit the same direction
- Returns `None` if no consensus reached

### 5. **RiskManager** — Risk Control (`src/trading_system.py`)

Validates trades and controls risk exposure.

**Validations:**
- Position count < `max_positions`
- Position value ≤ `max_position_size_pct` × portfolio value
- Sufficient available capital
- Daily loss < `max_daily_loss_pct` × initial capital

```python
size = risk_mgr.calculate_position_size(portfolio_value, risk_amount, stop_loss_distance)
valid, reason = risk_mgr.validate_trade(portfolio, ticker, quantity, price, stop_loss)
can_open, reason = risk_mgr.can_open_position(portfolio, position_value)
```

### 6. **OrderManager** — Order Execution (`src/trading_system.py`)

Manages the order queue.

```python
order = order_mgr.place_order(ticker, order_type, side, quantity, price)
order_mgr.execute_order(order, execution_price)
order_mgr.cancel_order(order_id)
pending = order_mgr.get_pending_orders(ticker)
```

### 7. **TradeLogger** — Performance Analysis (`src/trading_system.py`)

Reads from `portfolio.closed_positions` and computes statistics.

```python
stats = trade_logger.get_trade_statistics()
trade_logger.print_trade_summary()
```

### 8. **IndicatorCalculator** — Technical Indicators (`src/indicator_calculator.py`)

Stateless; all methods are `@staticmethod`. `calculate_all(df)` adds 19 columns to the DataFrame.

### 9. **Visualization** — Charts (`src/visualization.py`)

Four chart dashboards saved as PNG files. Called by `save_report()` and `save_charts()`.

### 10. **Logger** — Structured Logging (`src/logger.py`)

```python
from src.logger import get_logger
log = get_logger("my_module")
```
Writes to `logs/trading_system.log` (rotating, 5 MB × 5 files) and stdout.

---

## Configuration

### Basic Configuration

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(
    initial_capital=50000,           # Starting capital
    ticker="TSLA",                   # Stock to trade
    max_positions=5,                 # Max concurrent positions
    max_position_size_pct=0.10       # Max 10% per position
)

# Configure risk management
system.risk_manager.max_daily_loss_pct = 0.03  # Stop if down 3%

# Run backtest
results = system.backtest(
    start_date="2022-01-01",
    end_date="2024-01-31",
    signal_timeframe="daily"
)
```

### Using Risk Profile YAMLs

```python
import yaml
from src.automated_trading_system import AutomatedTradingSystem

with open("config/risk_profiles.yml") as f:
    profiles = yaml.safe_load(f)

profile = profiles["aggressive"]
system = AutomatedTradingSystem(
    initial_capital=10000,
    ticker="AAPL",
    max_positions=profile["max_positions"],
    max_position_size_pct=profile["max_position_size_pct"],
)
system.risk_manager.max_daily_loss_pct = profile["max_daily_loss_pct"]
```

### Adjusting Signal Sensitivity

```python
# More signals (lower bar)
system.signal_generator.confidence_threshold = 0.50

# Fewer, higher-quality signals
system.signal_generator.confidence_threshold = 0.65

# Reweight scoring components
from src.signal_generator import SignalGenerator
SignalGenerator.WEIGHTS['trend_alignment'] = 0.30
SignalGenerator.WEIGHTS['momentum'] = 0.20
```

---

## Usage Examples

### Example 1: Backtest a Single Stock

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="MSFT")
results = system.backtest(start_date="2023-01-01", end_date="2023-12-31")
system.print_detailed_results()

portfolio = results['portfolio']
trades = results['trades']
print(f"Total Return: {portfolio['return_pct']:.2f}%")
print(f"Win Rate: {trades['win_rate']:.2f}%")
print(f"Profit Factor: {trades['profit_factor']:.2f}")
```

### Example 2: Multi-Stock Backtesting

```python
from src.automated_trading_system import AutomatedTradingSystem
import pandas as pd

tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
results = {}

for ticker in tickers:
    print(f"Backtesting {ticker}...")
    system = AutomatedTradingSystem(initial_capital=10000, ticker=ticker)
    results[ticker] = system.backtest("2023-06-01", "2024-01-31")

comparison = pd.DataFrame({
    ticker: {
        'Return': results[ticker]['portfolio']['return_pct'],
        'Win_Rate': results[ticker]['trades']['win_rate'],
        'Total_Trades': results[ticker]['trades']['total_trades'],
        'Profit_Factor': results[ticker]['trades']['profit_factor']
    }
    for ticker in tickers
}).T

print(f"\n{comparison}")
```

### Example 3: Generate Real-Time Signal

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(ticker="AAPL")
system.fetch_realtime_data(lookback_days=365)
system.calculate_indicators()

signal = system.generate_signals()   # returns Signal | None

if signal:
    print(f"Signal: {signal.signal_type} @ ${signal.entry_price:.2f}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"Stop: ${signal.stop_loss:.2f}  Target: ${signal.take_profit:.2f}")
    print(f"Timeframe: {signal.timeframe}")
    for reason in signal.reason:
        print(f"  {reason}")
else:
    print("No signal generated — conditions not met.")
```

### Example 4: Manual Trade Execution

```python
from src.automated_trading_system import AutomatedTradingSystem
from src.signal_generator import Signal
from datetime import datetime

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")

signal = Signal(
    ticker="AAPL",
    timestamp=datetime.now(),
    signal_type="BUY",
    confidence=0.85,
    strength=28.5,
    entry_price=150.00,
    stop_loss=145.00,
    take_profit=160.00,
    reason=["Manual signal for testing"]
)

system.execute_signal(signal)
system.print_portfolio_status()

# Close the position manually
system.close_position("Manual Exit", 155.00)
```

### Example 5: Generate Report

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=25000, ticker="NVDA")
system.backtest("2023-01-01", "2024-01-01")

run_folder = system.save_report("2023-01-01", "2024-01-01")
print(f"\nOpen report: {run_folder}/report.md")
```

---

## Advanced Features

### 1. Multi-Timeframe Analysis

The system automatically combines weekly, daily, and 4h signals. You can inspect each:

```python
# After calculate_indicators(), inspect per-timeframe data
for tf in ['daily', 'weekly', '4h']:
    if tf in system.indicators:
        df = system.indicators[tf]
        print(f"{tf}: {len(df)} bars, last close ${df['Close'].iloc[-1]:.2f}")
```

### 2. Custom Risk Management Rules

```python
system.risk_manager.max_positions = 10
system.risk_manager.max_position_size_pct = 0.05
system.risk_manager.max_daily_loss_pct = 0.05

# Check manually before executing
valid, reason = system.risk_manager.validate_trade(
    system.portfolio, "AAPL", shares, price, stop_loss
)
if valid:
    print("Trade valid")
else:
    print(f"Rejected: {reason}")
```

### 3. Portfolio Analysis

```python
summary = system.portfolio.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")
print(f"Return: {summary['return_pct']:.2f}%")
print(f"Realized P&L: ${summary['realized_pnl']:+,.2f}")
print(f"Unrealized P&L: ${summary['unrealized_pnl']:+,.2f}")

for trade in system.portfolio.closed_positions:
    print(f"{trade.ticker} {trade.side} | "
          f"Entry ${trade.entry_price:.2f} → Exit ${trade.exit_price:.2f} | "
          f"P&L ${trade.profit_loss:+.2f} | {trade.exit_signal}")
```

### 4. Signal Confidence Analysis

```python
import numpy as np

confidences = [s.confidence for s in system.signals_history]
if confidences:
    print(f"Avg Confidence: {np.mean(confidences):.1%}")
    print(f"Min Confidence: {np.min(confidences):.1%}")
    print(f"Max Confidence: {np.max(confidences):.1%}")
    high = sum(1 for c in confidences if c > 0.80)
    print(f"High Confidence Signals (>80%): {high}")
```

### 5. Exporting Data

```python
# Export trades to CSV
csv_path = system.export_trades()
print(f"Trades: {csv_path}")

# JSON backtest results are auto-saved during backtest()
# Find them in data/backtest_results/

# Clear download cache
removed = system.clear_cache("AAPL")
print(f"Cleared {removed} cache file(s)")
```

---

## Troubleshooting

### Issue: "No data found for ticker"
```python
import yfinance as yf

df = yf.download("AAPL", start="2023-01-01", end="2023-12-31", progress=False)
print(df.head())  # Should show OHLCV data

# Use correct ticker symbol (e.g., "AAPL" not "APPLE")
```

### Issue: "Insufficient capital to open position"
```python
# Reduce position size
system.risk_manager.max_position_size_pct = 0.02  # 2%

# Or increase capital
system = AutomatedTradingSystem(initial_capital=100000)
```

### Issue: "No signals generated"
```python
# Check indicator data is populated
df = system.indicators.get('daily')
if df is not None:
    print(df[['Close', 'RSI', 'MACD', 'ADX']].tail(10))

# Lower threshold temporarily (not recommended for live trading)
system.signal_generator.confidence_threshold = 0.45

# Ensure ADX is above 15 (required)
print(f"ADX range: {df['ADX'].min():.1f} – {df['ADX'].max():.1f}")
```

### Issue: "Stale data / wrong prices"
```python
# Clear the cache and re-fetch
system.clear_cache("AAPL")
system.fetch_data(start_date, end_date)
```

### Issue: "Slow Performance"
```python
# Use a shorter date range for testing
system.backtest(start_date="2023-06-01", end_date="2024-01-31")

# Data is cached after first fetch — subsequent runs on same range are fast
```

---

## Performance Metrics Explained

### Profit Factor
- **Formula:** Gross Wins / Gross Losses
- **Target:** >1.5
- **Example:** 2.0 means $2 won per $1 lost

### Win Rate
- **Formula:** Winning Trades / Total Trades × 100
- **Target:** >50% (especially when profit factor is solid)

### Max Drawdown
- **Formula:** (Peak Equity − Trough Equity) / Peak Equity × 100
- **Target:** <20%
- Maximum loss from any equity peak

### Avg Holding Days
- Average number of days a position is held
- Depends on strategy style (swing vs trend following)

---

## Next Steps

1. **Backtest on historical data** — Validate strategy before risking capital
2. **Paper trade** — Generate live signals without executing real trades
3. **Live trading** — Start with minimum position sizes
4. **Monitor and adjust** — Review logs and reports regularly
5. **Risk management** — Never risk more than you can afford to lose

---

## Disclaimer

This system is for educational and research purposes.

- Backtest thoroughly before live trading
- Start with small position sizes
- Use stop losses on every trade
- Never trade with money you cannot afford to lose
- Consult a licensed financial advisor for investment decisions
- Past performance does not guarantee future results
