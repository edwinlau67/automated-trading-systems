import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import our modules
from trading_system import (
    PortfolioManager, RiskManager, OrderManager, TradeLogger,
    OrderType, OrderSide, Position, Trade
)
from signal_generator import SignalGenerator, Signal, MultiTimeframeSignalAnalyzer

# ============================================================================
# TECHNICAL INDICATORS CALCULATOR
# ============================================================================

class IndicatorCalculator:
    """Calculate all technical indicators"""
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators for a dataframe"""
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # Trend Indicators
        df['SMA_20'] = IndicatorCalculator.sma(close, 20)
        df['SMA_50'] = IndicatorCalculator.sma(close, 50)
        df['SMA_200'] = IndicatorCalculator.sma(close, 200)
        df['EMA_12'] = IndicatorCalculator.ema(close, 12)
        df['EMA_26'] = IndicatorCalculator.ema(close, 26)
        
        # Momentum Indicators
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = IndicatorCalculator.macd(close)
        df['RSI'] = IndicatorCalculator.rsi(close, 14)
        df['RSI_Divergence'] = IndicatorCalculator.rsi_divergence(df['RSI'], close)
        
        # Volatility Indicators
        df['ATR'] = IndicatorCalculator.atr(high, low, close, 14)
        df['ADX'], df['Plus_DI'], df['Minus_DI'] = IndicatorCalculator.adx(high, low, close, 14)
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = IndicatorCalculator.bollinger_bands(close, 20, 2)
        
        # Oscillators
        df['Stoch_K'], df['Stoch_D'] = IndicatorCalculator.stochastic(high, low, close, 14)
        
        return df
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def rsi_divergence(rsi: pd.Series, price: pd.Series, window: int = 14) -> pd.Series:
        divergence = pd.Series(0, index=rsi.index)
        
        for i in range(window * 2, len(rsi)):
            # Bullish divergence
            if (price.iloc[i-window:i].min() < price.iloc[i-window*2:i-window].min() and 
                rsi.iloc[i-window:i].min() > rsi.iloc[i-window*2:i-window].min()):
                divergence.iloc[i] = 1
            # Bearish divergence
            elif (price.iloc[i-window:i].max() > price.iloc[i-window*2:i-window].max() and 
                  rsi.iloc[i-window:i].max() < rsi.iloc[i-window*2:i-window].max()):
                divergence.iloc[i] = -1
        
        return divergence
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
        plus_dm = high.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm = -low.diff()
        minus_dm[minus_dm < 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2):
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=3).mean()
        return k, d


# ============================================================================
# AUTOMATED TRADING SYSTEM
# ============================================================================

class AutomatedTradingSystem:
    """Complete automated trading system orchestrator"""
    
    def __init__(self, initial_capital: float = 10000, ticker: str = "AAPL",
                 max_positions: int = 5, max_position_size_pct: float = 0.05):
        """
        Initialize the trading system
        
        Args:
            initial_capital: Starting portfolio value
            ticker: Stock ticker to trade
            max_positions: Maximum concurrent positions
            max_position_size_pct: Max % of portfolio per trade
        """
        
        self.ticker = ticker
        self.portfolio = PortfolioManager(initial_capital)
        self.risk_manager = RiskManager(
            max_positions=max_positions,
            max_position_size_pct=max_position_size_pct
        )
        self.order_manager = OrderManager(self.portfolio)
        self.trade_logger = TradeLogger(self.portfolio)
        
        self.signal_generator = SignalGenerator()
        self.mtf_analyzer = MultiTimeframeSignalAnalyzer()
        
        self.data = {}
        self.indicators = {}
        self.signals_history = []
        
        self.last_signal = None
        self.in_position = False
        self.position_id = None
        
        print(f"✓ Trading System Initialized")
        print(f"  Capital: ${initial_capital:,.2f}")
        print(f"  Ticker: {ticker}")
        print(f"  Max Positions: {max_positions}")
    
    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================
    
    def fetch_data(self, start_date: str, end_date: str) -> bool:
        """Fetch historical data from Yahoo Finance"""
        
        try:
            print(f"\n📊 Fetching data for {self.ticker}...")
            
            # Fetch daily data
            daily_data = yf.download(
                self.ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if daily_data.empty:
                print(f"✗ No data found for {self.ticker}")
                return False

            if isinstance(daily_data.columns, pd.MultiIndex):
                daily_data.columns = daily_data.columns.get_level_values(0)

            self.data['daily'] = daily_data.copy()
            
            # Create other timeframes
            self.data['weekly'] = daily_data.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            self.data['4h'] = daily_data.resample('4h').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna() if len(daily_data) > 50 else pd.DataFrame()
            
            print(f"✓ Data fetched successfully")
            print(f"  Daily bars: {len(daily_data)}")
            print(f"  Date range: {daily_data.index[0].date()} to {daily_data.index[-1].date()}")
            
            return True
        
        except Exception as e:
            print(f"✗ Error fetching data: {e}")
            return False

    def fetch_realtime_data(self, lookback_days: int = 365) -> bool:
        """Fetch data up to today, then patch the latest bar with live quote."""
        end_date = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        if not self.fetch_data(start_date, end_date):
            return False

        # Overwrite today's close with the live price if market data is available
        try:
            info = yf.Ticker(self.ticker).fast_info
            live_price = info.last_price
            if live_price and not pd.isna(live_price):
                today = pd.Timestamp(datetime.today().date())
                daily = self.data['daily']
                if today in daily.index:
                    daily.at[today, 'Close'] = live_price
                else:
                    # Market open today but daily bar not yet in download — append it
                    new_row = daily.iloc[-1].copy()
                    new_row['Close'] = live_price
                    new_row.name = today
                    self.data['daily'] = pd.concat([daily, new_row.to_frame().T])
                print(f"  Live price: ${live_price:.2f}")
        except Exception:
            pass  # Non-fatal; historical close is still usable

        return True

    def calculate_indicators(self) -> bool:
        """Calculate all technical indicators for all timeframes"""
        
        try:
            print(f"\n📈 Calculating indicators...")
            
            for timeframe, df in self.data.items():
                if df.empty:
                    continue
                
                self.indicators[timeframe] = IndicatorCalculator.calculate_all(df.copy())
            
            print(f"✓ Indicators calculated for {len(self.indicators)} timeframes")
            return True
        
        except Exception as e:
            print(f"✗ Error calculating indicators: {e}")
            return False
    
    # ========================================================================
    # SIGNAL GENERATION
    # ========================================================================
    
    def generate_signals(self, use_only_latest: bool = False) -> Optional[Signal]:
        """Generate trading signals for all timeframes"""
        
        signals = {}
        
        for timeframe in ['weekly', 'daily', '4h']:
            if timeframe not in self.indicators:
                continue
            
            df = self.indicators[timeframe]
            
            # Generate signal for latest bar
            signal = self.signal_generator.generate_signal(df, -1, timeframe)
            
            if signal:
                signal.ticker = self.ticker
                signals[timeframe] = signal
                self.signal_generator.signal_history.append(signal)
            else:
                signals[timeframe] = None
        
        # Analyze confluence
        if len([s for s in signals.values() if s]) > 0:
            combined_signal = self.mtf_analyzer.get_combined_signal(signals)
            
            if combined_signal:
                combined_signal.ticker = self.ticker
                self.signals_history.append(combined_signal)
                return combined_signal
        
        return None
    
    def display_latest_signal(self, signal: Optional[Signal] = None):
        """Display the latest signal"""
        
        if not signal:
            signal = self.signals_history[-1] if self.signals_history else None
        
        if not signal:
            print("\n⚪ No signals generated")
            return
        
        print("\n" + "="*70)
        print(f"SIGNAL: {signal}")
        print("="*70)
        print(f"Timeframe:    {signal.timeframe}")
        print(f"Confidence:   {signal.confidence:.1%}")
        print(f"Strength:     {signal.strength:.2f} (ADX)")
        print(f"\nPrice Targets:")
        print(f"  Entry:      ${signal.entry_price:.2f}")
        print(f"  Stop Loss:  ${signal.stop_loss:.2f}")
        print(f"  Take Profit:${signal.take_profit:.2f}")
        print(f"\nReason:")
        for reason in signal.reason:
            print(f"  • {reason}")
    
    # ========================================================================
    # TRADE EXECUTION
    # ========================================================================
    
    def execute_signal(self, signal: Signal) -> bool:
        """Execute trade based on signal"""
        
        if signal.signal_type not in ["BUY", "SELL"]:
            return False
        
        # Check if already in position
        if self.in_position:
            print(f"⚠ Already in position, skipping signal")
            return False
        
        # Calculate position size
        stop_loss_distance = abs(signal.entry_price - signal.stop_loss)
        risk_amount = self.portfolio.total_value * 0.02  # 2% risk per trade
        position_size = self.risk_manager.calculate_position_size(
            self.portfolio.total_value,
            risk_amount,
            stop_loss_distance
        )
        
        # Validate trade
        valid, reason = self.risk_manager.validate_trade(
            self.portfolio,
            signal.ticker,
            position_size,
            signal.entry_price,
            signal.stop_loss
        )
        
        if not valid:
            print(f"✗ Trade validation failed: {reason}")
            return False
        
        # Open position
        position = self.portfolio.open_position(
            ticker=signal.ticker,
            entry_price=signal.entry_price,
            quantity=position_size,
            side="LONG" if signal.signal_type == "BUY" else "SHORT",
            signal=signal.reason[0] if signal.reason else "",
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit
        )
        
        if position:
            self.in_position = True
            self.position_id = position.position_id
            self.last_signal = signal
            
            print(f"\n✓ Trade executed successfully")
            print(f"  Position ID: {position.position_id}")
            print(f"  Size: {position_size:.2f} shares")
            print(f"  Risk: ${risk_amount:.2f}")
            
            return True
        
        return False
    
    def check_exit_conditions(self, current_price: float) -> bool:
        """Check if open position should be closed"""
        
        if not self.in_position or not self.position_id:
            return False
        
        position = self.portfolio.positions.get(self.position_id)
        if not position:
            return False
        
        # Update position
        self.portfolio.update_position(self.position_id, current_price)
        
        # Check stop loss
        if position.stop_loss > 0:
            if position.side == "LONG" and current_price <= position.stop_loss:
                self.close_position("Stop Loss Hit", current_price)
                return True
            elif position.side == "SHORT" and current_price >= position.stop_loss:
                self.close_position("Stop Loss Hit", current_price)
                return True
        
        # Check take profit
        if position.take_profit > 0:
            if position.side == "LONG" and current_price >= position.take_profit:
                self.close_position("Take Profit Hit", current_price)
                return True
            elif position.side == "SHORT" and current_price <= position.take_profit:
                self.close_position("Take Profit Hit", current_price)
                return True
        
        return False
    
    def close_position(self, reason: str, exit_price: float):
        """Close open position"""
        
        if not self.in_position or not self.position_id:
            return
        
        trade = self.portfolio.close_position(self.position_id, exit_price, reason)
        
        if trade:
            self.in_position = False
            self.position_id = None
    
    # ========================================================================
    # BACKTESTING
    # ========================================================================
    
    def backtest(self, start_date: str, end_date: str, 
                 signal_timeframe: str = 'daily') -> Dict:
        """Run backtest on historical data"""
        
        print("\n" + "="*70)
        print("BACKTESTING")
        print("="*70)
        
        # Fetch and prepare data
        if not self.fetch_data(start_date, end_date):
            return {}
        
        if not self.calculate_indicators():
            return {}
        
        df = self.indicators[signal_timeframe].copy()
        
        # Backtest loop
        for idx in range(50, len(df)):
            current_row = df.iloc[idx]
            current_price = current_row['Close']
            
            # Check exit conditions
            if self.in_position:
                self.check_exit_conditions(current_price)
            
            # Check for new signals
            if not self.in_position:
                signal = self.signal_generator.generate_signal(df, idx, signal_timeframe)
                
                if signal:
                    signal.ticker = self.ticker
                    signal.entry_price = current_price
                    self.signals_history.append(signal)
                    self.execute_signal(signal)
        
        # Close any remaining position
        if self.in_position and self.position_id:
            final_price = df.iloc[-1]['Close']
            self.close_position("Backtest End", final_price)
        
        # Return statistics
        return self.get_backtest_results()
    
    def get_backtest_results(self) -> Dict:
        """Get detailed backtest results"""
        
        stats = self.trade_logger.get_trade_statistics()
        summary = self.portfolio.get_portfolio_summary()
        
        results = {
            'portfolio': summary,
            'trades': stats,
            'signals': self.signal_generator.get_signal_summary()
        }
        
        return results
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def print_portfolio_status(self):
        """Print current portfolio status"""
        
        summary = self.portfolio.get_portfolio_summary()
        
        print("\n" + "="*70)
        print("PORTFOLIO STATUS")
        print("="*70)
        print(f"\nCapital:")
        print(f"  Initial:     ${summary['initial_capital']:>12,.2f}")
        print(f"  Current:     ${summary['total_value']:>12,.2f}")
        print(f"  Cash:        ${summary['cash']:>12,.2f}")
        print(f"  Return:      {summary['return_pct']:>12.2f}%")
        
        print(f"\nPositions:")
        print(f"  Open:        {summary['open_positions']:>12}")
        print(f"  Closed:      {summary['closed_trades']:>12}")
        print(f"  Unrealized:  ${summary['unrealized_pnl']:>12,.2f}")
        print(f"  Realized:    ${summary['realized_pnl']:>12,.2f}")
    
    def print_detailed_results(self):
        """Print detailed backtest results"""
        
        self.print_portfolio_status()
        self.trade_logger.print_trade_summary()
        
        print("\n" + "="*70)
        print("SIGNAL SUMMARY")
        print("="*70)
        
        signal_stats = self.signal_generator.get_signal_summary()
        print(f"\nTotal Signals:     {signal_stats['total_signals']}")
        print(f"Buy Signals:       {signal_stats['buy_signals']}")
        print(f"Sell Signals:      {signal_stats['sell_signals']}")
        print(f"Avg Confidence:    {signal_stats['avg_confidence']:.1%}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """Run example trading system"""
    
    # Create system
    system = AutomatedTradingSystem(
        initial_capital=10000,
        ticker="AAPL",
        max_positions=3,
        max_position_size_pct=0.05
    )
    
    # Run backtest
    print("\nStarting backtest...")
    results = system.backtest(
        start_date="2023-06-01",
        end_date="2024-01-31",
        signal_timeframe="daily"
    )
    
    # Print results
    system.print_detailed_results()


if __name__ == "__main__":
    main()
