# API Reference

## AutomatedTradingSystem

**Module:** `src.automated_trading_system`

### Constructor

```python
AutomatedTradingSystem(
    initial_capital: float = 10000,
    ticker: str = "AAPL",
    max_positions: int = 5,
    max_position_size_pct: float = 0.05,
)
```

### Methods

#### `fetch_data(start_date, end_date) -> bool`
Download and resample OHLCV data for daily, weekly, and 4h timeframes.
Results are cached under `data/cache/` keyed by ticker + date range.
Returns `True` on success, `False` if download returns empty.

#### `fetch_realtime_data(lookback_days=365) -> bool`
Fetch recent data ending today; patches today's bar with the live quote if available.

#### `calculate_indicators() -> bool`
Compute all technical indicators on every available timeframe.
Populates `self.indicators` dict keyed by timeframe (`'daily'`, `'weekly'`, `'4h'`).

#### `generate_signals(use_only_latest=False) -> Signal | None`
Run `SignalGenerator` across timeframes, combine via `MultiTimeframeSignalAnalyzer`,
and return the combined `Signal` if consensus is reached, otherwise `None`.

#### `display_latest_signal(signal=None)`
Pretty-print signal details (type, timeframe, confidence, entry/stop/target, reasons).

#### `execute_signal(signal: Signal) -> bool`
Validate and execute a single signal through `RiskManager` and `PortfolioManager`.
Returns `True` if a position was opened.

#### `check_exit_conditions(current_price: float) -> bool`
Check whether the open position's stop-loss or take-profit has been hit.

#### `close_position(reason: str, exit_price: float)`
Close the currently tracked open position.

#### `backtest(start_date, end_date, signal_timeframe='daily') -> dict`
Full backtest pipeline: fetch → indicators → signals → execute → save results.
Returns dict with keys: `portfolio`, `trades`, `signals`.
Results are also saved as JSON under `data/backtest_results/`.

#### `get_backtest_results() -> dict`
Return the results dict without re-running the backtest.

#### `save_report(start_date='', end_date='') -> str`
Generate four chart PNGs and a `report.md` in `runs/<TICKER>_<timestamp>/`.
Returns the run folder path.

#### `save_charts(prefix='') -> list[str]`
Save all four chart dashboards and return their file paths.

#### `export_trades() -> str`
Export closed trades to `data/exports/<TICKER>_trades_<timestamp>.csv`.
Returns the file path, or empty string if no closed trades.

#### `clear_cache(ticker=None) -> int`
Delete cached CSV files. Pass a ticker to clear only that ticker, or `None` to clear all.
Returns the number of files removed.

#### `print_portfolio_status()`
Print current portfolio state to stdout.

#### `print_detailed_results()`
Print portfolio status, trade summary, and signal statistics to stdout.

---

## IndicatorCalculator

**Module:** `src.indicator_calculator`

All methods are `@staticmethod`.

### `calculate_all(df: DataFrame) -> DataFrame`
The single public entry point. Calls all helpers below and returns `df` with columns added in-place.

Added columns: `SMA_20`, `SMA_50`, `SMA_200`, `EMA_12`, `EMA_26`, `MACD`, `MACD_Signal`,
`MACD_Histogram`, `RSI`, `RSI_Divergence`, `ATR`, `ADX`, `Plus_DI`, `Minus_DI`,
`BB_Upper`, `BB_Middle`, `BB_Lower`, `Stoch_K`, `Stoch_D` (19 total).

### Individual helpers

| Method | Signature | Returns |
|--------|-----------|---------|
| `sma` | `(data: Series, period: int) -> Series` | Simple moving average |
| `ema` | `(data: Series, period: int) -> Series` | Exponential moving average |
| `macd` | `(data: Series, fast=12, slow=26, signal=9) -> (Series, Series, Series)` | macd_line, signal_line, histogram |
| `rsi` | `(data: Series, period=14) -> Series` | RSI 0–100 |
| `rsi_divergence` | `(rsi: Series, price: Series, window=14) -> Series` | +1 bullish, -1 bearish, 0 none |
| `atr` | `(high: Series, low: Series, close: Series, period=14) -> Series` | Average True Range |
| `adx` | `(high: Series, low: Series, close: Series, period=14) -> (Series, Series, Series)` | adx, plus_di, minus_di |
| `bollinger_bands` | `(data: Series, period=20, std_dev=2) -> (Series, Series, Series)` | upper, middle, lower |
| `stochastic` | `(high: Series, low: Series, close: Series, period=14) -> (Series, Series)` | %K, %D |

---

## Signal (dataclass)

**Module:** `src.signal_generator`

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | str | Stock symbol |
| `timestamp` | datetime | Signal time |
| `signal_type` | str | `"BUY"` or `"SELL"` |
| `confidence` | float | 0.0–1.0 |
| `strength` | float | ADX value at signal time |
| `entry_price` | float | Suggested entry |
| `stop_loss` | float | Stop loss price |
| `take_profit` | float | Take profit price |
| `reason` | list[str] | Human-readable indicator reasons |
| `timeframe` | str | Source timeframe (`"daily"`, `"weekly"`, `"4h"`, `"multi"`) |

---

## IndicatorSnapshot (dataclass)

**Module:** `src.signal_generator`

Internal snapshot used by `SignalGenerator` to pass indicator values between scoring methods.
Fields mirror the column names added by `IndicatorCalculator.calculate_all()`.

---

## SignalGenerator

**Module:** `src.signal_generator`

### Constructor

```python
SignalGenerator(confidence_threshold: float = 0.55)
```

### Public Methods

#### `generate_signal(df, current_row_idx, timeframe='daily') -> Signal | None`
Analyze indicators at row `current_row_idx` and return a Signal if confidence ≥ threshold.
Requires at least 50 rows before `current_row_idx`.

#### `get_signal_summary() -> dict`
Return statistics: `total_signals`, `buy_signals`, `sell_signals`, `avg_confidence`.

### Attributes

| Attribute | Description |
|-----------|-------------|
| `confidence_threshold` | Minimum score to emit a signal (default 0.55) |
| `signal_history` | List of all `Signal` objects generated |
| `WEIGHTS` | Class-level dict of scoring component weights |

### Signal Scoring Weights

```python
WEIGHTS = {
    'trend_alignment': 0.25,
    'momentum':        0.25,
    'reversal':        0.20,
    'volatility':      0.15,  # maps to ADX/trend-strength component
    'volume':          0.15,  # maps to price-action component
}
```

---

## MultiTimeframeSignalAnalyzer

**Module:** `src.signal_generator`

### Constructor

```python
MultiTimeframeSignalAnalyzer()
```

Creates internal `SignalGenerator` instances for `'weekly'`, `'daily'`, and `'4h'`.

### Methods

| Method | Signature | Returns |
|--------|-----------|---------|
| `get_confluence_score` | `(signals: dict[str, Signal\|None]) -> float` | Weighted confidence score 0–1 |
| `analyze_confluence` | `(signals: dict[str, Signal\|None]) -> (str, float)` | `(signal_type, confidence)` where type is `"BUY"`, `"SELL"`, or `"HOLD"` |
| `get_combined_signal` | `(signals: dict[str, Signal\|None]) -> Signal\|None` | Combined multi-timeframe signal, or `None` if no consensus |

`get_combined_signal` requires agreement from at least 2 timeframes to emit a signal.

---

## PortfolioManager

**Module:** `src.trading_system`

### Constructor

```python
PortfolioManager(
    initial_capital: float,
    use_margin: bool = False,
    margin_multiplier: float = 2.0,
)
```

### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `open_position` | `(ticker, entry_price, quantity, side='LONG', signal='', stop_loss=None, take_profit=None) -> Position\|None` | Open a new position; returns `None` if insufficient capital |
| `close_position` | `(position_id, exit_price, exit_signal='') -> Trade\|None` | Close position at given price; returns the completed `Trade` |
| `update_position` | `(position_id, current_price)` | Refresh unrealized P&L and `days_held` |
| `update_portfolio_value` | `() -> float` | Recompute `total_value` from cash + open positions |
| `get_portfolio_summary` | `() -> dict` | Return dict of current portfolio metrics |
| `create_snapshot` | `() -> PortfolioSnapshot` | Append and return a `PortfolioSnapshot` |

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_value` | float | Cash + sum of position market values |
| `cash` | float | Available cash |
| `equity` | float | Same as `total_value` |
| `initial_capital` | float | Starting capital |
| `positions` | dict[str, Position] | Open positions keyed by `position_id` |
| `closed_positions` | list[Trade] | Completed trades |
| `trades` | list[Trade] | Same list (alias) |
| `portfolio_history` | list[PortfolioSnapshot] | Snapshots from `create_snapshot()` |
| `use_margin` | bool | Whether margin is enabled |
| `margin_multiplier` | float | Leverage multiplier when margin is enabled |

### `get_portfolio_summary()` keys

`timestamp`, `total_value`, `initial_capital`, `cash`, `equity`, `return_pct`,
`open_positions`, `closed_trades`, `unrealized_pnl`, `realized_pnl`,
`margin_used`, `margin_available`.

---

## RiskManager

**Module:** `src.trading_system`

### Constructor

```python
RiskManager(
    max_positions: int = 10,
    max_position_size_pct: float = 0.05,
    max_daily_loss_pct: float = 0.02,
    max_correlation: float = 0.7,
)
```

Note: `AutomatedTradingSystem` passes `max_positions=5` by default.

### Key Methods

| Method | Signature | Returns |
|--------|-----------|---------|
| `calculate_position_size` | `(portfolio_value, risk_amount, stop_loss_distance) -> float` | Number of shares (risk-based, capped at `max_position_size_pct`) |
| `can_open_position` | `(portfolio, position_value) -> (bool, str)` | Pass/fail with reason string |
| `check_daily_loss_limit` | `(portfolio) -> bool` | `True` if within daily limit |
| `validate_trade` | `(portfolio, ticker, quantity, price, stop_loss) -> (bool, str)` | Full pre-trade validation |

---

## OrderManager

**Module:** `src.trading_system`

### Constructor

```python
OrderManager(portfolio: PortfolioManager)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `place_order` | `(ticker, order_type, side, quantity, price, stop_price=None, take_profit=None, stop_loss=None) -> Order\|None` | Create and queue a pending order |
| `execute_order` | `(order: Order, execution_price: float) -> bool` | Mark order as filled |
| `cancel_order` | `(order_id: str) -> bool` | Cancel and remove a pending order |
| `get_pending_orders` | `(ticker=None) -> list[Order]` | Return pending orders, optionally filtered by ticker |

`order_type` is `OrderType.MARKET`, `OrderType.LIMIT`, `OrderType.STOP`, or `OrderType.STOP_LIMIT`.
`side` is `OrderSide.BUY` or `OrderSide.SELL`.

---

## TradeLogger

**Module:** `src.trading_system`

### Constructor

```python
TradeLogger(portfolio: PortfolioManager)
```

Reads trades from `portfolio.closed_positions` — no independent state.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_trade_statistics` | `() -> dict` | Return win_rate, profit_factor, avg_win/loss, largest_win/loss, avg_holding_days |
| `print_trade_summary` | `()` | Print full TRADING SYSTEM SUMMARY to stdout |

### `get_trade_statistics()` keys

`total_trades`, `winning_trades`, `losing_trades`, `win_rate`, `profit_factor`,
`avg_win`, `avg_loss`, `total_profit`, `largest_win`, `largest_loss`, `avg_holding_days`.

---

## Position (dataclass)

**Module:** `src.trading_system`

| Field | Type | Description |
|-------|------|-------------|
| `position_id` | str | Unique ID (`POS_<n>_<ticker>`) |
| `ticker` | str | Stock symbol |
| `entry_date` | datetime | When position was opened |
| `entry_price` | float | Entry price |
| `quantity` | float | Number of shares |
| `side` | str | `"LONG"` or `"SHORT"` |
| `entry_signal` | str | Signal reason text |
| `stop_loss` | float | Stop loss price (0 if unset) |
| `take_profit` | float | Take profit price (0 if unset) |
| `unrealized_pnl` | float | Current unrealized P&L |
| `current_price` | float | Last updated price |
| `days_held` | int | Days since entry |

---

## Trade (dataclass)

**Module:** `src.trading_system`

| Field | Type | Description |
|-------|------|-------------|
| `trade_id` | str | Unique ID (`TRADE_<n>_<ticker>`) |
| `ticker` | str | Stock symbol |
| `entry_date` | datetime | Entry timestamp |
| `exit_date` | datetime\|None | Exit timestamp |
| `entry_price` | float | Entry price |
| `exit_price` | float | Exit price |
| `quantity` | float | Shares traded |
| `side` | str | `"LONG"` or `"SHORT"` |
| `profit_loss` | float | Dollar P&L |
| `return_pct` | float | Percent return |
| `status` | str | `"OPEN"` or `"CLOSED"` |
| `entry_signal` | str | Signal reason at entry |
| `exit_signal` | str | Exit reason (`"Stop Loss Hit"`, `"Take Profit Hit"`, etc.) |
| `holding_days` | int | Days held |
| `win` | bool | `profit_loss > 0` |
| `stop_loss` | float | Stop price at entry |
| `take_profit` | float | Target price at entry |

---

## Logger

**Module:** `src.logger`

```python
from src.logger import get_logger
log = get_logger("my_module")
log.info("message")
```

Two handlers on every logger:
- `RotatingFileHandler` — DEBUG+ → `logs/trading_system.log` (5 MB × 5 files)
- `StreamHandler` — INFO+ → stdout

---

## Visualization

**Module:** `src.visualization`

| Function | Signature | Description |
|----------|-----------|-------------|
| `plot_technical_indicators` | `(system, save_path='chart_indicators.png')` | 5-panel: price+MAs+BB+volume, MACD, RSI, ADX, Stochastic |
| `plot_signals` | `(system, save_path='chart_signals.png')` | 3-panel: price with signal markers, confidence bars, cumulative count |
| `plot_performance` | `(system, save_path='chart_performance.png')` | 6-panel: equity curve, drawdown, P&L distribution, summary bar, monthly heatmap |
| `plot_risk_management` | `(system, save_path='chart_risk.png')` | 4-panel: position sizes, entry/stop/target levels, daily P&L, risk/reward ratios |
| `plot_all` | `(system, prefix='') -> list[str]` | Save all four dashboards; returns file paths |

---

## Report

**Module:** `src.report`

```python
from src.report import generate_report
run_path = generate_report(system, start_date="2023-01-01", end_date="2024-01-01")
```

Creates `runs/<TICKER>_<YYYYMMDD_HHMMSS>/` containing:
- `report.md` — executive summary, indicator table, signal list, performance metrics, trade log
- `chart_indicators.png`
- `chart_signals.png`
- `chart_performance.png`
- `chart_risk.png`

Returns the run folder path.
