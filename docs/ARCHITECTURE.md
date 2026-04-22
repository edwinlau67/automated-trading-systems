# System Architecture

## Overview

The Automated Trading System is built as a layered pipeline. Each layer has a single responsibility and communicates through well-defined interfaces.

```
                   ┌──────────────────────────────────────────────┐
                   │        User / Examples / Notebooks           │
                   └──────────────────────┬───────────────────────┘
                                          │
  ╔═══════════════════════════════════════▼═════════════════════════════╗
  ║              AutomatedTradingSystem  (Orchestrator)                 ║
  ║                src/automated_trading_system.py                      ║
  ╠═════════════════════════════════════════════════════════════════════╣
  ║                                                                     ║
  ║  ┌─────────────┐   ┌─────────────────┐   ┌───────────────────────┐  ║
  ║  │ Data Layer  │──►│   Indicators    │──►│   Signal Generator    │  ║
  ║  │             │   │   Calculator    │   │                       │  ║
  ║  │ yfinance    │   │                 │   │  SignalGenerator      │  ║
  ║  │ + disk cache│   │  19 cols / TF   │   │  MTFAnalyzer          │  ║
  ║  │ daily/wk/4h │   │                 │   │                       │  ║
  ║  └─────────────┘   └─────────────────┘   └───────────┬───────────┘  ║
  ║                                                      │              ║
  ║                                          ┌───────────▼───────────┐  ║
  ║                                          │     RiskManager       │  ║
  ║                                          │   validate_trade()    │  ║
  ║                                          └───────────┬───────────┘  ║
  ║                                                      │              ║
  ║                                          ┌───────────▼───────────┐  ║
  ║                                          │  PortfolioManager     │  ║
  ║                                          │  OrderManager         │  ║
  ║                                          │  TradeLogger          │  ║
  ║                                          └───────────┬───────────┘  ║
  ║                                                      │              ║
  ║  ┌───────────────────────────────────────────────────▼───────────┐  ║
  ║  │       report.py  ·  visualization.py  ·  logger.py            │  ║
  ║  └───────────────────────────────────────────────────────────────┘  ║
  ║                                                                     ║
  ╚═════════════════════════════════════════════════════════════════════╝
```

---

## Component Map

### `src/automated_trading_system.py` — Orchestrator
- Entry point for all user workflows
- Calls each sub-component in order: fetch → indicators → signals → risk → portfolio → report
- Holds `self.data`, `self.indicators`, `self.signal_generator`, `self.portfolio`,
  `self.risk_manager`, `self.order_manager`, `self.trade_logger`, `self.mtf_analyzer`

### `src/indicator_calculator.py` — Indicators
- Stateless; all methods are `@staticmethod`
- `calculate_all(df)` is the single public entry point
- Adds 19 columns to the DataFrame in-place and returns it

### `src/signal_generator.py` — Signal Scoring
- `SignalGenerator` scores buy/sell potential per bar using a 5-component weighted model
- `MultiTimeframeSignalAnalyzer` combines per-timeframe signals into a single consensus signal
- `Signal` dataclass is the output contract

### `src/trading_system.py` — Portfolio & Risk
- `PortfolioManager`: tracks `Position` objects, computes equity, holds `closed_positions` list
- `RiskManager`: validates every trade before it touches the portfolio
- `OrderManager`: manages order queue; two-step place → execute lifecycle
- `TradeLogger`: reads from `portfolio.closed_positions` and computes statistics
- `Trade` dataclass is the immutable record of a completed round-trip

### `src/visualization.py` — Charts
- Four dashboard functions: `plot_technical_indicators`, `plot_signals`, `plot_performance`, `plot_risk_management`
- `plot_all(system)` saves all four in one call
- Uses `matplotlib` with Agg backend (headless / file output only)

### `src/report.py` — Markdown Report
- `generate_report(system)` creates a timestamped run folder under `runs/`
- Calls all four visualization functions, then writes `report.md`
- Includes executive summary, indicator table, signal list, trade log

### `src/logger.py` — Structured Logging
- `get_logger(name)` returns a child of the root `trading_system` logger
- Two handlers: rotating file (`logs/trading_system.log`) + console
- All `src/` modules use this for consistent log output

---

## Data Flow

```
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  1 · DATA ACQUISITION                                                ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  yfinance.download(ticker, start, end)                               ║
  ║    ├─ cache hit  ──► read  data/cache/<TICKER>_<dates>.csv           ║
  ║    └─ cache miss ──► fetch ──► write data/cache/                     ║
  ║  Resample ──► system.data['daily']  ·  ['weekly']  ·  ['4h']         ║
  ╚══════════════════════════════════╦═══════════════════════════════════╝
                                     ║
                                     ▼
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  2 · INDICATOR CALCULATION  (IndicatorCalculator.calculate_all)      ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  Trend     │ SMA 20/50/200  ·  EMA 12/26                             ║
  ║  Momentum  │ MACD  ·  MACD Signal  ·  MACD Histogram  ·  RSI         ║
  ║  Oscillat. │ Stochastic %K  ·  Stochastic %D                         ║
  ║  Volatil.  │ ATR  ·  Bollinger Upper / Middle / Lower                ║
  ║  Strength  │ ADX  ·  +DI  ·  −DI  ·  RSI Divergence    [19 cols]     ║
  ╚══════════════════════════════════╦═══════════════════════════════════╝
                                     ║
                                     ▼
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  3 · SIGNAL GENERATION  (per bar, per timeframe)                     ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  SignalGenerator.generate_signal()                                   ║
  ║                                                                      ║
  ║    Component          Weight   Inputs                                ║
  ║    ─────────────────────────────────────────────────────────────     ║
  ║    Trend Alignment     25%    SMA 20/50  ·  EMA 12/26                ║
  ║    Momentum            25%    MACD  ·  RSI  ·  Stochastic            ║
  ║    Reversal            20%    RSI divergence  ·  Bollinger extremes  ║
  ║    Volatility / ADX    15%    ADX  (suppressed if ADX < 15)          ║
  ║    Price Action        15%    Higher / lower highs and lows          ║
  ║    ─────────────────────────────────────────────────────────────     ║
  ║    Combined score ≥ 0.55  ──►  Signal emitted                        ║
  ║                                                                      ║
  ║  MultiTimeframeSignalAnalyzer.get_combined_signal()                  ║
  ║    weekly ──┐                                                        ║
  ║    daily  ──┼──► ≥ 2 timeframes agree ──► combined Signal            ║
  ║    4h     ──┘                                                        ║
  ╚══════════════════════════════════╦═══════════════════════════════════╝
                                     ║
                                     ▼
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  4 · RISK VALIDATION  (RiskManager.validate_trade)                   ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  ✓  open positions  < max_positions                                  ║
  ║  ✓  position value  ≤ max_position_size_pct × portfolio value        ║
  ║  ✓  available cash  ≥ position value                                 ║
  ║  ✓  daily loss      < max_daily_loss_pct × initial capital           ║
  ╚══════════════════════════════════╦═══════════════════════════════════╝
                                     ║
                                     ▼
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  5 · EXECUTION  (PortfolioManager + OrderManager)                    ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  open_position()   ──► Position added to portfolio.positions         ║
  ║  check_exit()      ──► stop-loss / take-profit monitoring per bar    ║
  ║  close_position()  ──► Trade added to portfolio.closed_positions     ║
  ╚══════════════════════════════════╦═══════════════════════════════════╝
                                     ║
                                     ▼
  ╔══════════════════════════════════════════════════════════════════════╗
  ║  6 · REPORTING                                                       ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║  TradeLogger.get_trade_statistics()                                  ║
  ║  report.py         ──► runs/<TICKER>_<ts>/report.md + 4 chart PNGs   ║
  ║  _save_backtest_results() ──► data/backtest_results/*.json           ║
  ║  export_trades()   ──► data/exports/*.csv                            ║
  ╚══════════════════════════════════════════════════════════════════════╝
```

---

## Signal Scoring Model

Each bar generates a score for both BUY and SELL directions. The higher score wins if it clears the confidence threshold (0.55).

| Component | Weight | Inputs |
|-----------|--------|--------|
| Trend Alignment | 25% | Price vs SMA20/50, EMA12 vs EMA26 |
| Momentum | 25% | MACD histogram, RSI level, Stochastic %K/%D |
| Reversal | 20% | RSI divergence, Bollinger Band extremes |
| Volatility (ADX) | 15% | ADX strength; signal suppressed if ADX < 15 |
| Price Action | 15% | Higher highs/lows (BUY) or lower highs/lows (SELL) |

Multi-timeframe consensus requires at least 2 timeframes to emit the same direction.

---

## Risk Management Rules

Trades are rejected if any of these conditions fail:

1. **Position count** — open positions < `max_positions` (orchestrator default 5)
2. **Position size** — `quantity × price` ≤ `max_position_size_pct` × portfolio value (default 5%)
3. **Available capital** — sufficient cash (+ margin if enabled)
4. **Daily loss** — today's realized loss < `max_daily_loss_pct` × initial capital (default 2%)

---

## Configuration

Three YAML files in `config/`:

| File | Purpose |
|------|---------|
| `default_config.yml` | All system defaults |
| `risk_profiles.yml` | Conservative / moderate / aggressive presets |
| `indicators_config.yml` | Indicator periods and thresholds |

---

## Directory Structure

```
automated-trading-systems/
├── src/
│   ├── automated_trading_system.py   # Orchestrator
│   ├── trading_system.py             # Portfolio, Risk, Orders, TradeLogger
│   ├── signal_generator.py           # SignalGenerator, MultiTimeframeSignalAnalyzer
│   ├── indicator_calculator.py       # IndicatorCalculator (static methods)
│   ├── visualization.py              # Chart dashboards (matplotlib)
│   ├── report.py                     # Markdown report + chart generation
│   └── logger.py                     # Centralised logging setup
├── config/
│   ├── default_config.yml
│   ├── risk_profiles.yml
│   └── indicators_config.yml
├── data/
│   ├── cache/                        # yfinance CSV cache (keyed by ticker+dates)
│   ├── backtest_results/             # JSON results from every backtest() call
│   └── exports/                      # CSV trade exports from export_trades()
├── examples/
│   ├── 01_simple_backtest.py
│   ├── 02_multi_stock_comparison.py
│   ├── 03_custom_configuration.py
│   ├── 04_signal_generation.py
│   └── 05_advanced_analysis.py
├── notebooks/
│   ├── analysis.ipynb
│   ├── backtest_comparison.ipynb
│   └── optimization.ipynb
├── logs/
│   └── trading_system.log            # Rotating log (5 MB × 5 files)
├── runs/
│   └── <TICKER>_<YYYYMMDD_HHMMSS>/  # Per-run output folders
│       ├── report.md
│       ├── chart_indicators.png
│       ├── chart_signals.png
│       ├── chart_performance.png
│       └── chart_risk.png
├── tests/
├── requirements.txt
└── PROJECT_STRUCTURE.md
```

---

## Output Structure

Every `backtest()` call produces two outputs:

1. **JSON result** — saved to `data/backtest_results/<TICKER>_<start>_<end>_<ts>.json`

2. **Run folder** (via `save_report()`) — `runs/<TICKER>_<YYYYMMDD_HHMMSS>/`
   ```
   chart_indicators.png    # Technical indicators dashboard
   chart_signals.png       # Signal generation dashboard
   chart_performance.png   # Equity curve, drawdown, trade stats
   chart_risk.png          # Position sizing, daily P&L, R:R ratios
   report.md               # Full Markdown report
   ```

`backtest()` also populates:
- `system.data` — raw OHLCV DataFrames per timeframe
- `system.indicators` — indicator-enriched DataFrames per timeframe
- `system.portfolio.closed_positions` — list of `Trade` objects
- `system.portfolio.total_value` — final equity
- `system.signals_history` — list of `Signal` objects generated
