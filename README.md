# Automated Trading System

A Python-based automated trading system with multi-timeframe technical analysis, confidence-scored signal generation, and rule-based risk management. Supports historical backtesting and live signal generation.

---

## Project Structure

```
automated-trading-systems/
├── src/                        # Core library
│   ├── automated_trading_system.py  # Main orchestrator
│   ├── trading_system.py            # Portfolio, risk, orders
│   ├── signal_generator.py          # Signal scoring engine
│   └── indicator_calculator.py      # 12+ technical indicators
├── examples/                   # Runnable example scripts
│   ├── 01_simple_backtest.py
│   ├── 02_multi_stock_comparison.py
│   ├── 03_custom_configuration.py
│   ├── 04_signal_generation.py
│   └── 05_advanced_analysis.py
├── tests/                      # 65 unit + integration tests
├── config/                     # YAML configuration files
├── docs/                       # Full documentation
├── report.py                   # Per-run Markdown report generator
├── visualization.py            # Chart dashboard (4 panels)
└── requirements.txt
```

---

## Quick Start

```bash
git clone https://github.com/edwinlau67/automated-trading-systems.git
cd automated-trading-systems
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python examples/01_simple_backtest.py
```

---

## Usage

### Backtest

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
results = system.backtest("2023-01-01", "2024-01-01")
system.print_detailed_results()
```

### Real-Time Signal

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(ticker="AAPL")
system.fetch_realtime_data(lookback_days=365)
system.calculate_indicators()
signals = system.generate_signals()
if signals:
    s = signals[-1]
    print(f"{s.signal_type}  confidence={s.confidence:.1%}  entry=${s.entry_price:.2f}  stop=${s.stop_loss:.2f}  target=${s.take_profit:.2f}")
```

### Multi-Stock Comparison

```python
import pandas as pd
from src.automated_trading_system import AutomatedTradingSystem

rows = {}
for ticker in ["AAPL", "MSFT", "GOOGL", "TSLA"]:
    system = AutomatedTradingSystem(10000, ticker)
    r = system.backtest("2023-01-01", "2024-01-01")
    rows[ticker] = {"Return %": r["portfolio"]["return_pct"], "Win Rate %": r["trades"]["win_rate"]}

print(pd.DataFrame(rows).T)
```

### Custom Risk Config

```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(
    initial_capital=50000, ticker="TSLA",
    max_positions=3, max_position_size_pct=0.10
)
system.risk_manager.max_daily_loss_pct = 0.01
system.backtest("2023-01-01", "2024-01-01")
system.print_detailed_results()
```

---

## Technical Indicators

| Category | Indicators |
|----------|-----------|
| Trend | SMA (20, 50, 200), EMA (12, 26) |
| Momentum | MACD (12/26/9), RSI (14), Stochastic (14) |
| Volatility | ATR (14), Bollinger Bands (20/2σ) |
| Trend Strength | ADX (14), +DI, -DI |
| Pattern | RSI Divergence, Support/Resistance |

---

## Signal Scoring

Signals require ≥ 55% confidence across five weighted components:

| Component | Weight |
|-----------|--------|
| Trend alignment (price vs. MAs) | 25% |
| Momentum (MACD, RSI, Stochastic) | 25% |
| Reversal (divergences, S/R bounces) | 20% |
| Volatility (ADX, ATR, Bollinger) | 15% |
| Price action (HH/HL, breakouts) | 15% |

Multi-timeframe confluence (weekly + daily agreement) adds up to +15%.

---

## Risk Management

- Position size capped at `max_position_size_pct` of portfolio (default 5%)
- Maximum concurrent open positions (default 5)
- Daily loss limit halts trading (default 2% of capital)
- Minimum risk/reward ratio of 1.5 enforced on every trade

---

## Running Tests

```bash
pytest tests/ -v
# 65 passed
```

---

## Documentation

| File | Contents |
|------|---------|
| `docs/TRADING_SYSTEM_GUIDE.md` | Complete user guide |
| `docs/QUICK_REFERENCE.md` | Quick lookup for common tasks |
| `docs/API_REFERENCE.md` | Full API reference |
| `docs/ARCHITECTURE.md` | System design and data flow |
| `docs/EXAMPLES.md` | Annotated code examples |

---

## Disclaimer

For educational and research purposes only. Past performance does not guarantee future results. All trading involves risk of loss.
