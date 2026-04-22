# Automated Trading System - Project Structure

## Project Overview

**Project Name:** Automated Multi-Timeframe Trading System  
**Version:** 1.0.0  
**Status:** Complete & Production-Ready  
**Created:** April 2026  
**Language:** Python 3.13+  

---

## 📁 Project Directory Structure

```
automated-trading-systems/
│
├── README.md                           # Quick start guide
├── START_HERE.txt                      # Step-by-step getting started guide (read first!)
├── PROJECT_STRUCTURE.md                # This file
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git ignore patterns
│
├── src/                                # Source code
│   ├── __init__.py
│   ├── automated_trading_system.py     # Main orchestrator (585 lines)
│   ├── trading_system.py               # Portfolio management (588 lines)
│   ├── signal_generator.py             # Signal generation (493 lines)
│   ├── indicator_calculator.py         # Technical indicators (119 lines)
│   ├── visualization.py                # Chart dashboards (648 lines)
│   ├── report.py                       # Per-run report & chart output (368 lines)
│   └── logger.py                       # Centralised logging setup (65 lines)
│
├── docs/                               # Documentation
│   ├── TRADING_SYSTEM_GUIDE.md         # Complete guide
│   ├── QUICK_REFERENCE.md              # Quick reference
│   ├── API_REFERENCE.md                # Generated API docs
│   ├── ARCHITECTURE.md                 # System architecture
│   └── EXAMPLES.md                     # Code examples
│
├── examples/                           # Example scripts
│   ├── 01_simple_backtest.py           # Basic backtest example
│   ├── 02_multi_stock_comparison.py    # Compare multiple stocks
│   ├── 03_custom_configuration.py      # Custom setup example
│   ├── 04_signal_generation.py         # Generate real-time signals
│   └── 05_advanced_analysis.py         # Advanced usage
│
├── tests/                              # Unit & integration tests
│   ├── test_trading_system.py
│   ├── test_signal_generator.py
│   ├── test_indicators.py
│   ├── test_portfolio.py
│   ├── test_examples.py
│   └── test_readme_examples.py
│
├── data/                               # Data files (git-ignored content)
│   ├── backtest_results/               # Backtest outputs
│   ├── cache/                          # Cached market data
│   └── exports/                        # Exported trades
│
├── config/                             # Configuration files
│   ├── default_config.yml              # Default settings
│   ├── risk_profiles.yml               # Risk management profiles
│   └── indicators_config.yml           # Indicator parameters
│
├── notebooks/                          # Jupyter notebooks
│   ├── analysis.ipynb                  # Data analysis
│   ├── backtest_comparison.ipynb       # Strategy comparison
│   └── optimization.ipynb              # Parameter optimization
│
├── runs/                               # Per-run output (git-ignored)
│   └── <TICKER>_<YYYYMMDD>_<HHMMSS>/  # Timestamped run folder
│       ├── report.md                   # Markdown performance report
│       ├── chart_indicators.png        # Price + indicators chart
│       ├── chart_signals.png           # Buy/sell signal chart
│       ├── chart_performance.png       # Equity curve chart
│       └── chart_risk.png              # Drawdown / risk chart
│
└── logs/                               # Log files
    └── trading_system.log
```

---

## 🎯 Project Goals

### Primary Goals
1. ✅ Create a complete automated trading system
2. ✅ Implement multi-timeframe technical analysis
3. ✅ Generate intelligent trading signals
4. ✅ Manage risk automatically
5. ✅ Provide comprehensive backtesting
6. ✅ Track portfolio performance

### Secondary Goals
1. ✅ Educational resource for learning trading systems
2. ✅ Demonstrate software engineering best practices
3. ✅ Provide clear, comprehensive documentation
4. ✅ Support easy customization
5. ✅ Enable paper trading capabilities

---

## 📦 Core Components

### 1. **AutomatedTradingSystem** (Main Orchestrator)
**File:** `src/automated_trading_system.py` (585 lines)

**Responsibilities:**
- Coordinate all system components
- Fetch and manage market data
- Calculate technical indicators
- Generate trading signals
- Execute trades
- Run backtests
- Generate reports

**Key Classes:**
- `AutomatedTradingSystem` - Main class

**Key Methods:**
- `fetch_data()` - Get historical data
- `calculate_indicators()` - Compute indicators
- `generate_signals()` - Create trading signals
- `execute_signal()` - Execute trades
- `backtest()` - Run backtesting
- `print_detailed_results()` - Print results summary

---

### 2. **TradingSystem** (Portfolio & Position Management)
**File:** `src/trading_system.py` (588 lines)

**Responsibilities:**
- Manage portfolio positions
- Track cash and equity
- Calculate P&L
- Manage orders
- Log trades
- Calculate performance metrics

**Key Classes:**
- `PortfolioManager` - Portfolio tracking
- `Position` - Individual position tracking
- `Trade` - Completed trade records
- `RiskManager` - Risk control
- `OrderManager` - Order handling
- `TradeLogger` - Trade analysis

**Key Methods:**
- `open_position()` - Open new position
- `close_position()` - Close position
- `update_position()` - Update metrics
- `validate_trade()` - Validate before execution
- `get_portfolio_summary()` - Portfolio stats

---

### 3. **SignalGenerator** (Technical Analysis)
**File:** `src/signal_generator.py` (493 lines)

**Responsibilities:**
- Analyze technical indicators
- Generate buy/sell signals
- Score signal confidence
- Detect divergences
- Multi-timeframe confluence

**Key Classes:**
- `SignalGenerator` - Main signal engine
- `Signal` - Signal data structure
- `IndicatorSnapshot` - Indicator values
- `MultiTimeframeSignalAnalyzer` - MTF analysis

**Key Methods:**
- `generate_signal()` - Create signal
- `analyze_buy_signal()` - Buy analysis
- `analyze_sell_signal()` - Sell analysis
- `analyze_confluence()` - MTF confirmation
- `get_signal_summary()` - Signal statistics

---

### 4. **IndicatorCalculator** (Technical Indicators)
**File:** `src/indicator_calculator.py` (119 lines)

**Responsibilities:**
- Compute all technical indicators from OHLCV data
- Return a single enriched DataFrame consumed by the rest of the system

**Key Functions:**
- `calculate_indicators(df)` - Adds 12+ indicator columns to the price DataFrame

---

### 5. **Visualization** (Chart Dashboards)
**File:** `src/visualization.py` (648 lines)

**Responsibilities:**
- Render multi-panel chart dashboards
- Save charts to per-run output folders

**Key Functions:**
- `plot_technical_indicators(system)` - Price + indicators panel
- `plot_signals(system)` - Buy/sell signal overlay
- `plot_performance(system)` - Equity curve
- `plot_risk(system)` - Drawdown and risk metrics

---

### 6. **Report** (Per-Run Output)
**File:** `src/report.py` (368 lines)

**Responsibilities:**
- Create a timestamped `runs/<TICKER>_<timestamp>/` folder
- Write a Markdown performance report
- Save all four chart PNGs into that folder

**Key Functions:**
- `generate_report(system)` - Orchestrates report + chart generation

---

### 7. **Logger** (Centralised Logging)
**File:** `src/logger.py` (65 lines)

**Responsibilities:**
- Provide a single `get_logger(name)` factory used by every module
- Route output to both console and `logs/trading_system.log`

**Key Functions:**
- `get_logger(name)` - Returns a configured `logging.Logger`

---

## 📊 Technical Architecture

### Data Flow

```
Yahoo Finance API
       ↓
   Data Layer
       ↓
IndicatorCalculator (12+ indicators)
       ↓
SignalGenerator (AI-based scoring)
       ↓
MultiTimeframeAnalyzer (Confluence)
       ↓
RiskManager (Validation)
       ↓
OrderManager (Execution)
       ↓
PortfolioManager (Tracking)
       ↓
TradeLogger (Analysis)
       ↓
Report + Visualization (runs/<ticker>_<ts>/)
```

### Component Interaction

```
User Code
   ↓
AutomatedTradingSystem
   ├─→ IndicatorCalculator
   ├─→ SignalGenerator
   ├─→ RiskManager
   ├─→ PortfolioManager
   │   ├─→ Position Tracking
   │   ├─→ P&L Calculation
   │   └─→ TradeLogger
   ├─→ OrderManager
   ├─→ Visualization
   └─→ Report
```

---

## 🔧 Configuration System

### Default Configuration
**File:** `config/default_config.yml`

```yaml
portfolio:
  initial_capital: 10000
  use_margin: false
  margin_multiplier: 2.0

risk_management:
  max_positions: 5
  max_position_size_pct: 0.05
  max_daily_loss_pct: 0.02
  max_correlation: 0.7

indicators:
  sma_periods: [20, 50, 200]
  ema_periods: [12, 26]
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  atr_period: 14
  adx_period: 14
  bollinger_period: 20
  bollinger_std: 2
  stochastic_period: 14

signals:
  confidence_threshold: 0.55
  trend_weight: 0.25
  momentum_weight: 0.25
  reversal_weight: 0.20
  volatility_weight: 0.15
  volume_weight: 0.15

backtesting:
  default_timeframe: 'daily'
  supported_timeframes: ['weekly', 'daily', '4h']
```

---

## 📈 Technical Indicators Implemented

### Trend Indicators
- Simple Moving Average (SMA): 20, 50, 200 periods
- Exponential Moving Average (EMA): 12, 26 periods

### Momentum Indicators
- MACD (12, 26, 9)
- RSI (14 period)
- Stochastic Oscillator (14 period)

### Volatility Indicators
- Average True Range (ATR): 14 period
- Average Directional Index (ADX): 14 period
- Bollinger Bands: 20 period, 2 standard deviations

### Pattern Detection
- RSI Divergence Detection
- Support/Resistance Levels
- Price Action Analysis

---

## 🎯 Signal Generation Algorithm

### Signal Scoring Model

**Trend Alignment (25%)**
- Price vs moving averages
- EMA crossovers
- Trend direction confirmation

**Momentum (25%)**
- MACD histogram
- RSI readings
- Stochastic signals

**Reversal (20%)**
- RSI divergences
- Support/resistance bounces
- Pattern recognition

**Volatility (15%)**
- ADX trend strength
- ATR levels
- Bollinger Band extremes

**Price Action (15%)**
- Higher highs/lows
- Lower highs/lows
- Breakout patterns

**Confidence Threshold:** ≥0.55 (55%) minimum

---

## 🚀 Features & Capabilities

### Trading Features
- ✅ Long and short positions
- ✅ Automatic position sizing
- ✅ Stop loss/take profit management
- ✅ Margin trading (optional)
- ✅ Multi-timeframe analysis
- ✅ Signal generation

### Risk Management
- ✅ Daily loss limits
- ✅ Position limits
- ✅ Capital validation
- ✅ Position sizing
- ✅ Margin controls
- ✅ Risk/reward validation

### Analysis
- ✅ Real-time metrics
- ✅ Trade statistics
- ✅ Performance metrics
- ✅ Signal analysis
- ✅ Equity curve tracking

### Data & Backtesting
- ✅ Yahoo Finance integration
- ✅ Multiple timeframes
- ✅ Historical data (100+ years available)
- ✅ Trade-by-trade analysis
- ✅ Performance reporting

### Output & Visualization
- ✅ Per-run timestamped output folders (`runs/`)
- ✅ Four chart dashboards (PNG)
- ✅ Markdown performance reports
- ✅ Structured log file

---

## 📊 Performance Metrics

### Portfolio Metrics
- Total Value
- Return Percentage
- Cash Position
- Unrealized P&L
- Realized P&L

### Trade Metrics
- Total Trades
- Winning Trades / Losing Trades
- Win Rate (%)
- Profit Factor
- Average Trade P&L
- Largest Win / Loss
- Average Holding Period

### Advanced Metrics
- Sharpe Ratio
- Max Drawdown
- Recovery Factor
- Profit/Loss Ratio

---

## 🧪 Testing Strategy

### Unit Tests
- Component testing
- Indicator calculation verification
- Signal generation validation
- Portfolio management testing
- Risk management validation

### Integration Tests
- End-to-end workflows
- Data flow verification
- Multi-component interactions
- Backtest consistency
- README and example script validation

---

## 📚 Documentation

### Comprehensive Guides
- **TRADING_SYSTEM_GUIDE.md** - Complete guide
- **QUICK_REFERENCE.md** - Quick lookup

### Technical Docs
- **API_REFERENCE.md** - Method reference
- **ARCHITECTURE.md** - System design
- **EXAMPLES.md** - Code examples
- **PROJECT_STRUCTURE.md** - This file

---

## 🔄 Workflow

### User Workflow
```
1. Install Dependencies
2. Read README.md
3. Run Examples
4. Backtest Strategy
5. Optimize Parameters
6. Paper Trade
7. Live Trade (with caution)
```

---

## 📦 Dependencies

### Core Dependencies
- **pandas** (2.1.4+) - Data analysis
- **numpy** (1.26.3+) - Numerical computing
- **yfinance** (0.2.32+) - Yahoo Finance data
- **scikit-learn** (1.3.2+) - Machine learning

### Optional Dependencies
- **matplotlib** (3.8.2+) - Visualization
- **seaborn** (0.13.0+) - Statistical plots
- **jupyter** - Notebooks
- **pytest** - Testing

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.13+
- pip or conda
- Internet connection (for Yahoo Finance)

### Installation Steps

```bash
# 1. Clone/download project
git clone <repo>

# 2. Navigate to project
cd automated-trading-systems

# 3. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python -c "import pandas; import yfinance; print('Ready')"

# 6. Run first example
python examples/01_simple_backtest.py
```

---

## 📖 Usage Examples

### Basic Backtest
```python
from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(initial_capital=10000, ticker="AAPL")
system.backtest(start_date="2023-06-01", end_date="2024-01-31")
system.print_detailed_results()
```

### Multi-Stock Comparison
```python
import pandas as pd

results = {}
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    system = AutomatedTradingSystem(10000, ticker)
    results[ticker] = system.backtest("2023-06-01", "2024-01-31")

comparison = pd.DataFrame({
    ticker: {
        'Return': r['portfolio']['return_pct'],
        'Win_Rate': r['trades']['win_rate']
    }
    for ticker, r in results.items()
}).T

print(comparison)
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

---

## ⚠️ Important Notes

### Safety
- Educational purposes only
- Backtest thoroughly before live trading
- Start with small position sizes
- Never trade money you can't afford to lose
- Monitor regularly

### Limitations
- Backtesting assumes perfect execution
- No slippage simulation
- Limited to US stocks on Yahoo Finance
- Technical analysis not 100% accurate
- Past performance ≠ future results

---

## 📞 Project Resources

### Main Files
1. `src/automated_trading_system.py` - Main system
2. `src/trading_system.py` - Portfolio management
3. `src/signal_generator.py` - Signal generation
4. `src/indicator_calculator.py` - Technical indicators
5. `src/visualization.py` - Chart dashboards
6. `src/report.py` - Per-run report output
7. `src/logger.py` - Logging setup

### Documentation
1. `docs/TRADING_SYSTEM_GUIDE.md` - Complete guide
2. `docs/QUICK_REFERENCE.md` - Quick reference
3. `docs/API_REFERENCE.md` - API reference

### Examples
1. `examples/01_simple_backtest.py` - Basic example
2. `examples/02_multi_stock_comparison.py` - Compare stocks
3. `examples/03_custom_configuration.py` - Custom setup

---

## 📄 License & Attribution

**Status:** Educational Software  
**For:** Learning and personal use  
**Disclaimer:** Use at your own risk. Not financial advice.

---

**Project Version:** 1.0.0  
**Last Updated:** April 2026  
**Status:** Complete
