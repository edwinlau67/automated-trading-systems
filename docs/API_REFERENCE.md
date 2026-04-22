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
- Returns `True` on success, `False` if download returns empty.

#### `fetch_realtime_data(lookback_days=365) -> bool`
Fetch recent data ending today. Equivalent to `fetch_data` with dynamic dates.

#### `calculate_indicators() -> bool`
Compute all technical indicators on every available timeframe.
- Populates `self.indicators` dict keyed by timeframe.

#### `generate_signals() -> list[Signal]`
Run `SignalGenerator` over the daily timeframe and return all signals generated.

#### `execute_signal(signal: Signal) -> bool`
Validate and execute a single signal through `RiskManager` and `PortfolioManager`.
- Returns `True` if trade was opened/closed.

#### `backtest(start_date, end_date) -> dict`
Full backtest pipeline: fetch → indicators → signals → execute → report.
- Returns dict with keys: `portfolio`, `trades`, `signals`.

#### `print_detailed_results()`
Print formatted backtest summary to stdout.

---

## IndicatorCalculator

**Module:** `src.indicator_calculator`

All methods are static.

| Method | Signature | Returns |
|--------|-----------|---------|
| `calculate_all` | `(df: DataFrame) -> DataFrame` | df with all indicator columns added |
| `sma` | `(series, period) -> Series` | Simple moving average |
| `ema` | `(series, period) -> Series` | Exponential moving average |
| `macd` | `(series, fast, slow, signal) -> (Series, Series, Series)` | macd_line, signal_line, histogram |
| `rsi` | `(series, period) -> Series` | RSI 0–100 |
| `rsi_divergence` | `(price, rsi, lookback) -> Series` | +1 bullish, -1 bearish, 0 none |
| `atr` | `(df, period) -> Series` | Average True Range |
| `adx` | `(df, period) -> (Series, Series, Series)` | adx, plus_di, minus_di |
| `bollinger_bands` | `(series, period, std_dev) -> (Series, Series, Series)` | upper, middle, lower |
| `stochastic` | `(df, period) -> (Series, Series)` | %K, %D |

---

## SignalGenerator

**Module:** `src.signal_generator`

### Constructor

```python
SignalGenerator(confidence_threshold: float = 0.55)
```

### Methods

#### `generate_signal(df, idx, timeframe) -> Signal | None`
Analyze indicators at row `idx` and return a Signal if confidence >= threshold.

#### `analyze_buy_signal(row) -> float`
Return buy score 0–1 based on 5-component weighted model.

#### `analyze_sell_signal(row) -> float`
Return sell score 0–1 based on 5-component weighted model.

#### `analyze_confluence(daily_df, weekly_df, idx) -> float`
Return multi-timeframe alignment bonus (0–0.15).

#### `get_signal_summary() -> dict`
Return statistics: total_signals, buy_signals, sell_signals, avg_confidence.

---

## Signal (dataclass)

**Module:** `src.signal_generator`

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | str | Stock symbol |
| `timestamp` | datetime | Signal time |
| `signal_type` | str | `"BUY"` or `"SELL"` |
| `confidence` | float | 0.0–1.0 |
| `strength` | float | Raw score before threshold |
| `entry_price` | float | Suggested entry |
| `stop_loss` | float | Stop loss price |
| `take_profit` | float | Take profit price |
| `reason` | list[str] | Human-readable reasons |

---

## PortfolioManager

**Module:** `src.trading_system`

### Constructor

```python
PortfolioManager(initial_capital: float = 10000)
```

### Key Methods

| Method | Description |
|--------|-------------|
| `open_position(ticker, side, shares, price, stop_loss, take_profit)` | Open a new position |
| `close_position(ticker, price, reason)` | Close position at given price |
| `update_position(ticker, current_price)` | Refresh unrealized P&L |
| `get_portfolio_summary()` | Return dict of portfolio metrics |

### Key Properties

| Property | Description |
|----------|-------------|
| `total_value` | Cash + sum of position market values |
| `cash` | Available cash |
| `positions` | dict of open `Position` objects |
| `closed_trades` | list of completed `Trade` objects |

---

## RiskManager

**Module:** `src.trading_system`

### Constructor

```python
RiskManager(
    max_positions: int = 5,
    max_position_size_pct: float = 0.05,
    max_daily_loss_pct: float = 0.02,
    max_correlation: float = 0.7,
)
```

### Key Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_position_size(capital, price, risk_pct, stop_loss)` | int (shares) | Kelly-inspired sizing |
| `validate_trade(portfolio, signal)` | (bool, str) | Pass/fail with reason |
| `can_open_position(portfolio)` | bool | Check position count limit |
| `check_daily_loss_limit(portfolio)` | bool | True if within daily limit |

---

## OrderManager

**Module:** `src.trading_system`

### Methods

| Method | Description |
|--------|-------------|
| `place_order(ticker, side, order_type, shares, price, stop_loss, take_profit)` | Create pending order |
| `execute_order(order_id, portfolio)` | Execute a pending order |
| `cancel_order(order_id)` | Cancel a pending order |
| `get_pending_orders()` | Return list of pending orders |

---

## TradeLogger

**Module:** `src.trading_system`

### Methods

| Method | Description |
|--------|-------------|
| `log_trade(trade)` | Record a closed trade |
| `get_trade_stats()` | Return win_rate, profit_factor, avg_trade, etc. |
| `get_equity_curve(initial_capital)` | Return list of cumulative equity values |

---

## MultiTimeframeSignalAnalyzer

**Module:** `src.signal_generator`

### Methods

| Method | Description |
|--------|-------------|
| `analyze(daily_df, weekly_df, idx)` | Return confluence score 0–1 |
| `get_timeframe_alignment(daily_df, weekly_df, idx)` | Return per-timeframe trend dict |
