# CLAUDE.md

We're building the app described in @PROJECT_STRUCTURE.md. Read that file for general architectural tasks or to double-check the exact database structure, tech stack or application architecture.

Keep your replies extremely concise and focus on conveying the key information. No unnecessary fluff, no long code snippets.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_trading_system.py -v

# Run a single test
pytest tests/test_trading_system.py::TestPortfolioManager::test_initial_state -v

# Run an example
python examples/01_simple_backtest.py
```

## Architecture

The system is a layered pipeline orchestrated by `AutomatedTradingSystem` in `src/automated_trading_system.py`. Each stage outputs structured data consumed by the next:

```
Data (yfinance + cache) → IndicatorCalculator → SignalGenerator → RiskManager → PortfolioManager → report.py / visualization.py
```

**`src/automated_trading_system.py`** — single entry point for all user workflows. Holds references to all sub-components and drives the fetch → indicators → signals → risk → portfolio → report sequence. All cross-cutting state (`self.data`, `self.indicators`, `self.signals_history`, `self.portfolio`) lives here.

**`src/indicator_calculator.py`** — stateless; all methods are `@staticmethod`. `calculate_all(df)` adds 19 columns to a DataFrame in-place (SMA 20/50/200, EMA 12/26, MACD, RSI, Stochastic, ATR, Bollinger, ADX/+DI/-DI, RSI divergence) and returns it.

**`src/signal_generator.py`** — `SignalGenerator` scores each bar using a 5-component weighted model (threshold ≥ 0.55); emits `Signal` dataclass objects. `MultiTimeframeSignalAnalyzer` requires ≥ 2 of 3 timeframes (weekly/daily/4h) to agree before emitting a combined signal.

**`src/trading_system.py`** — contains four classes: `PortfolioManager` (tracks open `Position` objects and `closed_positions`), `RiskManager` (validates every trade against position count, size, cash, and daily-loss limits), `OrderManager` (two-step place → execute queue), `TradeLogger` (computes statistics from `closed_positions`). `Trade` is the immutable dataclass for a completed round-trip.

**`src/visualization.py`** — four chart dashboard functions (`plot_technical_indicators`, `plot_signals`, `plot_performance`, `plot_risk_management`); uses matplotlib Agg backend (file output only, no display). `plot_all(system)` saves all four.

**`src/report.py`** — `generate_report(system)` creates `runs/<TICKER>_<ts>/` containing four PNGs and `report.md`.

**`src/logger.py`** — `get_logger(name)` returns a named child of the root `trading_system` logger. All `src/` modules use this.

## Key Data Structures

- `Signal` (dataclass in `signal_generator.py`) — the output contract between signal generation and risk/portfolio layers: `ticker`, `signal_type` (BUY/SELL/HOLD), `confidence`, `entry_price`, `stop_loss`, `take_profit`, `reason`.
- `system.data` — `dict` of DataFrames keyed by timeframe: `"daily"`, `"weekly"`, `"4h"`.
- `system.indicators` — same shape as `system.data` but with 19 additional indicator columns appended by `IndicatorCalculator.calculate_all`.
- Data cache: `data/cache/<TICKER>_<dates>.csv`. Backtest JSON results: `data/backtest_results/`. Trade CSV exports: `data/exports/`.

## Configuration

Three YAML files in `config/` control defaults:
- `default_config.yml` — capital, risk limits, indicator periods, signal weights, and backtesting defaults.
- `risk_profiles.yml` — conservative / moderate / aggressive presets.
- `indicators_config.yml` — indicator periods and thresholds.

Risk defaults: 5% max position size, 5 max concurrent positions, 2% daily loss limit, 1.5 minimum R:R ratio.

## Python Version

Requires Python 3.13+. Uses `pandas ≥ 3.0`, `numpy ≥ 2.4`, `yfinance ≥ 1.3`, `matplotlib ≥ 3.10`.
