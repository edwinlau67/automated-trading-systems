# System Architecture

## Overview

The Automated Trading System is built as a layered pipeline. Each layer has a single responsibility and communicates through well-defined interfaces.

```
┌─────────────────────────────────────────────────────┐
│                   User / Examples                   │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│          AutomatedTradingSystem (Orchestrator)       │
│   src/automated_trading_system.py                    │
└──┬─────────────┬──────────────┬──────────────┬──────┘
   │             │              │              │
   ▼             ▼              ▼              ▼
Data Layer  Indicator     Signal Gen     Portfolio
(yfinance)  Calculator    (confidence    Manager
            (12 indics)    scoring)      + Risk Mgr
```

---

## Component Map

### `src/automated_trading_system.py` — Orchestrator
- Entry point for all user workflows
- Calls each sub-component in order: fetch → indicators → signals → risk → portfolio → report
- Holds `self.data`, `self.indicators`, `self.signal_generator`, `self.portfolio`, `self.risk_manager`, `self.order_manager`

### `src/indicator_calculator.py` — Indicators
- Stateless; all methods are `@staticmethod`
- `calculate_all(df)` is the single public entry point
- Adds 20+ columns to the DataFrame in-place and returns it

### `src/signal_generator.py` — Signal Scoring
- `SignalGenerator` loops rows and scores buy/sell potential
- 5-component weighted model (see Signal Scoring below)
- `MultiTimeframeSignalAnalyzer` adds an alignment bonus from weekly data
- `Signal` dataclass is the output contract

### `src/trading_system.py` — Portfolio & Risk
- `PortfolioManager`: tracks `Position` objects and computes equity
- `RiskManager`: validates every trade before it touches the portfolio
- `OrderManager`: two-step place→execute lifecycle for orders
- `TradeLogger`: records closed trades and computes statistics
- `Trade` dataclass is the immutable record of a completed round-trip

---

## Data Flow

```
yfinance.download()
    │
    ▼
Resample to daily / weekly / 4h DataFrames
    │
    ▼
IndicatorCalculator.calculate_all()
    │  Adds: SMA20/50/200, EMA12/26, MACD, RSI, ATR, ADX,
    │        Bollinger Bands, Stochastic, RSI Divergence
    ▼
SignalGenerator.generate_signal() per row
    │  Score buy/sell → compare to threshold (0.55)
    │  MultiTimeframeSignalAnalyzer adds confluence bonus
    ▼
Signal object  (type, confidence, entry, stop, target)
    │
    ▼
RiskManager.validate_trade()
    │  Checks: position count, size limit, daily loss, risk/reward
    ▼
OrderManager.place_order() → execute_order()
    │
    ▼
PortfolioManager.open_position() / close_position()
    │
    ▼
TradeLogger.log_trade()
    │
    ▼
Reporting & Metrics  (report.py, visualization.py)
```

---

## Signal Scoring Model

Each bar generates a score for both BUY and SELL directions. The higher score wins if it clears the confidence threshold.

| Component | Weight | Inputs |
|-----------|--------|--------|
| Trend Alignment | 25% | Price vs SMA20/50/200, EMA crossover |
| Momentum | 25% | MACD histogram, RSI level, Stochastic %K/%D |
| Reversal | 20% | RSI divergence, Bollinger Band extremes |
| Volatility | 15% | ADX strength, ATR relative to price |
| Price Action | 15% | Higher highs/lows, breakout patterns |

Multi-timeframe confluence (weekly agrees with daily) adds up to +0.15 bonus.

---

## Risk Management Rules

Trades are rejected if any of these conditions fail:

1. **Position count** — open positions < `max_positions` (default 5)
2. **Position size** — shares × price ≤ `max_position_size_pct` × portfolio value (default 5%)
3. **Daily loss** — today's realized loss < `max_daily_loss_pct` × initial capital (default 2%)
4. **Risk/reward** — `|take_profit - entry| / |entry - stop_loss|` ≥ 1.5

---

## Configuration

Three YAML files in `config/`:

| File | Purpose |
|------|---------|
| `default_config.yml` | All system defaults |
| `risk_profiles.yml` | Conservative / moderate / aggressive presets |
| `indicators_config.yml` | Indicator periods and thresholds |

---

## Output Structure

Every `backtest()` call populates:
- `system.data` — raw OHLCV DataFrames per timeframe
- `system.indicators` — indicator-enriched DataFrames per timeframe
- `system.portfolio.closed_trades` — list of `Trade` objects
- `system.portfolio.total_value` — final equity

`report.py::generate_report()` writes a timestamped run folder:
```
runs/<TICKER>_<YYYYMMDD_HHMMSS>/
    technical_indicators.png
    signals.png
    performance.png
    risk_management.png
    report.md
```
