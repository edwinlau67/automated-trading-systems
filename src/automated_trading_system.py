import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from src.trading_system import (
    PortfolioManager, RiskManager, OrderManager, TradeLogger,
    OrderType, OrderSide, Position, Trade
)
from src.signal_generator import SignalGenerator, Signal, MultiTimeframeSignalAnalyzer
from src.indicator_calculator import IndicatorCalculator
from src.logger import get_logger

log = get_logger("orchestrator")

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
        
        log.info("Trading system initialised  ticker=%s  capital=$%.2f  max_positions=%d",
                 ticker, initial_capital, max_positions)
    
    # ========================================================================
    # DATA MANAGEMENT
    # ========================================================================
    
    def fetch_data(self, start_date: str, end_date: str) -> bool:
        """Fetch historical data from Yahoo Finance"""
        
        try:
            log.info("Fetching data  ticker=%s  %s -> %s", self.ticker, start_date, end_date)

            # Fetch daily data
            daily_data = yf.download(
                self.ticker,
                start=start_date,
                end=end_date,
                progress=False
            )

            if daily_data.empty:
                log.error("No data returned for %s", self.ticker)
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
            
            log.info("Data fetched  bars=%d  range=%s -> %s",
                     len(daily_data), daily_data.index[0].date(), daily_data.index[-1].date())
            return True

        except Exception as e:
            log.exception("Error fetching data for %s: %s", self.ticker, e)
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
                log.debug("Live price patched  %s  $%.2f", self.ticker, live_price)
        except Exception:
            pass  # Non-fatal; historical close is still usable

        return True

    def calculate_indicators(self) -> bool:
        """Calculate all technical indicators for all timeframes"""
        
        try:
            log.info("Calculating indicators  ticker=%s", self.ticker)

            for timeframe, df in self.data.items():
                if df.empty:
                    continue
                self.indicators[timeframe] = IndicatorCalculator.calculate_all(df.copy())

            log.info("Indicators ready  timeframes=%s", list(self.indicators.keys()))
            return True

        except Exception as e:
            log.exception("Error calculating indicators: %s", e)
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
            log.warning("Already in position — signal skipped  %s", signal.signal_type)
            return False
        
        # Calculate position size (shares)
        stop_loss_distance = abs(signal.entry_price - signal.stop_loss)
        risk_amount = self.portfolio.total_value * 0.02  # 2% risk per trade
        position_size = self.risk_manager.calculate_position_size(
            self.portfolio.total_value,
            risk_amount,
            stop_loss_distance
        )
        # Cap to max position size in share terms (calculate_position_size caps in
        # dollars, not shares, so we re-cap here to avoid validate_trade rejection)
        max_shares = (self.portfolio.total_value * self.risk_manager.max_position_size_pct) / signal.entry_price
        position_size = min(position_size, max_shares)
        
        # Validate trade
        valid, reason = self.risk_manager.validate_trade(
            self.portfolio,
            signal.ticker,
            position_size,
            signal.entry_price,
            signal.stop_loss
        )
        
        if not valid:
            log.warning("Trade validation failed  %s  reason=%s", signal.ticker, reason)
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
            
            log.info("Trade opened  %s  %s  shares=%.2f  entry=$%.2f  stop=$%.2f  target=$%.2f  risk=$%.2f",
                     signal.ticker, "LONG" if signal.signal_type == "BUY" else "SHORT",
                     position_size, signal.entry_price, signal.stop_loss,
                     signal.take_profit, risk_amount)
            
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
    
    def save_report(self, start_date: str = "", end_date: str = "") -> str:
        """Generate charts and a Markdown report in runs/<TICKER>_<timestamp>/. Returns folder path."""
        from src.report import generate_report
        return generate_report(self, start_date=start_date, end_date=end_date)

    def save_charts(self, prefix: str = "") -> list:
        """Save all four chart dashboards. Returns list of saved file paths."""
        from src.visualization import plot_all
        return plot_all(self, prefix=prefix)

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
