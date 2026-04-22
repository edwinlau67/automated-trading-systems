import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json
from abc import ABC, abstractmethod

from src.logger import get_logger

_log_portfolio = get_logger("portfolio")
_log_orders    = get_logger("orders")

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class OrderType(Enum):
    """Order types for trading"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderSide(Enum):
    """Buy or Sell"""
    BUY = "BUY"
    SELL = "SELL"

class PositionStatus(Enum):
    """Position states"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"

@dataclass
class Order:
    """Represents a single order"""
    order_id: str
    ticker: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    status: str = "PENDING"
    filled_quantity: float = 0.0
    avg_filled_price: float = 0.0
    stop_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    notes: str = ""

@dataclass
class Trade:
    """Represents a completed trade (entry + exit)"""
    trade_id: str
    ticker: str
    entry_date: datetime
    exit_date: Optional[datetime] = None
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    side: str = "LONG"  # LONG or SHORT
    profit_loss: float = 0.0
    return_pct: float = 0.0
    status: str = "OPEN"  # OPEN or CLOSED
    entry_signal: str = ""
    exit_signal: str = ""
    holding_days: int = 0
    win: bool = False
    stop_loss: float = 0.0
    take_profit: float = 0.0

@dataclass
class Position:
    """Represents an open position"""
    position_id: str
    ticker: str
    entry_date: datetime
    entry_price: float
    quantity: float
    side: str = "LONG"  # LONG or SHORT
    entry_signal: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    current_price: float = 0.0
    days_held: int = 0

@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time"""
    timestamp: datetime
    total_value: float
    cash: float
    equity: float
    open_positions: int
    margin_used: float = 0.0
    margin_available: float = 0.0
    unrealized_pnl: float = 0.0
    daily_pnl: float = 0.0


# ============================================================================
# PORTFOLIO & POSITION MANAGEMENT
# ============================================================================

class PortfolioManager:
    """Manages portfolio positions, cash, and equity"""
    
    def __init__(self, initial_capital: float, use_margin: bool = False, margin_multiplier: float = 2.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.equity = initial_capital
        self.total_value = initial_capital
        self.use_margin = use_margin
        self.margin_multiplier = margin_multiplier
        self.margin_used = 0.0
        self.margin_available = initial_capital * (margin_multiplier - 1) if use_margin else 0.0
        
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Trade] = []
        self.trades: List[Trade] = []
        self.orders: List[Order] = []
        self.portfolio_history: List[PortfolioSnapshot] = []
        
        self.trade_counter = 0
        self.position_counter = 0
    
    def open_position(self, ticker: str, entry_price: float, quantity: float, 
                     side: str = "LONG", signal: str = "", stop_loss: float = None, 
                     take_profit: float = None) -> Optional[Position]:
        """Open a new position"""
        
        position_cost = entry_price * quantity
        
        # Check if we have enough capital
        if position_cost > self.cash + self.margin_available:
            _log_portfolio.warning("Insufficient capital  ticker=%s  required=$%.2f  available=$%.2f",
                                   ticker, position_cost, self.cash + self.margin_available)
            return None
        
        # Deduct from available capital
        if position_cost <= self.cash:
            self.cash -= position_cost
        else:
            # Use margin
            margin_needed = position_cost - self.cash
            self.margin_used += margin_needed
            self.margin_available -= margin_needed
            self.cash = 0
        
        # Create position
        position_id = f"POS_{self.position_counter}_{ticker}"
        position = Position(
            position_id=position_id,
            ticker=ticker,
            entry_date=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            side=side,
            entry_signal=signal,
            stop_loss=stop_loss or 0,
            take_profit=take_profit or 0,
            status=PositionStatus.OPEN
        )
        
        self.positions[position_id] = position
        self.position_counter += 1
        
        _log_portfolio.info("Position opened  %s  %s  qty=%.2f  entry=$%.2f  stop=$%.2f  target=$%.2f",
                            ticker, side, quantity, entry_price,
                            stop_loss or 0, take_profit or 0)
        return position
    
    def close_position(self, position_id: str, exit_price: float, exit_signal: str = "") -> Optional[Trade]:
        """Close an open position"""
        
        if position_id not in self.positions:
            _log_portfolio.warning("Position not found  id=%s", position_id)
            return None
        
        position = self.positions[position_id]
        
        # Calculate P&L
        if position.side == "LONG":
            profit_loss = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            profit_loss = (position.entry_price - exit_price) * position.quantity
        
        return_pct = (exit_price - position.entry_price) / position.entry_price * 100
        if position.side == "SHORT":
            return_pct *= -1
        
        # Return cash
        exit_value = exit_price * position.quantity
        self.cash += exit_value
        
        # Return margin if used
        if self.margin_used > 0:
            margin_to_return = min(self.margin_used, exit_value)
            self.margin_used -= margin_to_return
            self.margin_available += margin_to_return
        
        # Create trade record
        holding_days = (datetime.now() - position.entry_date).days
        trade = Trade(
            trade_id=f"TRADE_{self.trade_counter}_{position.ticker}",
            ticker=position.ticker,
            entry_date=position.entry_date,
            exit_date=datetime.now(),
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            side=position.side,
            profit_loss=profit_loss,
            return_pct=return_pct,
            status="CLOSED",
            entry_signal=position.entry_signal,
            exit_signal=exit_signal,
            holding_days=holding_days,
            win=profit_loss > 0,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit
        )
        
        self.trades.append(trade)
        self.closed_positions.append(trade)
        self.trade_counter += 1
        
        # Update position status
        position.status = PositionStatus.CLOSED
        del self.positions[position_id]
        
        outcome = "WIN" if profit_loss > 0 else "LOSS"
        _log_portfolio.info("Position closed  %s  %s  %s  exit=$%.2f  pnl=$%+.2f  return=%+.2f%%  days=%d  reason=%s",
                            position.ticker, position.side, outcome,
                            exit_price, profit_loss, return_pct, holding_days, exit_signal)
        
        return trade
    
    def update_position(self, position_id: str, current_price: float):
        """Update position metrics with current price"""
        
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        position.current_price = current_price
        
        if position.side == "LONG":
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:  # SHORT
            position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
        
        position.unrealized_pnl_pct = position.unrealized_pnl / (position.entry_price * position.quantity) * 100
        position.days_held = (datetime.now() - position.entry_date).days
    
    def update_portfolio_value(self):
        """Update total portfolio value based on current positions"""
        
        # Calculate equity from open positions
        position_value = 0.0
        total_unrealized_pnl = 0.0
        
        for pos_id, position in self.positions.items():
            if position.side == "LONG":
                position_value += position.current_price * position.quantity
            else:  # SHORT
                position_value += (position.entry_price - position.current_price) * position.quantity
            
            total_unrealized_pnl += position.unrealized_pnl
        
        self.equity = self.cash + position_value
        self.total_value = self.cash + position_value
        
        return self.total_value
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        
        self.update_portfolio_value()
        
        total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        return {
            'timestamp': datetime.now(),
            'total_value': self.total_value,
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'equity': self.equity,
            'return_pct': (self.total_value - self.initial_capital) / self.initial_capital * 100,
            'open_positions': len(self.positions),
            'closed_trades': len(self.closed_positions),
            'unrealized_pnl': total_unrealized,
            'realized_pnl': sum(t.profit_loss for t in self.closed_positions),
            'margin_used': self.margin_used,
            'margin_available': self.margin_available
        }
    
    def create_snapshot(self) -> PortfolioSnapshot:
        """Create portfolio snapshot for history"""
        
        summary = self.get_portfolio_summary()
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            total_value=summary['total_value'],
            cash=summary['cash'],
            equity=summary['equity'],
            open_positions=summary['open_positions'],
            unrealized_pnl=summary['unrealized_pnl']
        )
        
        self.portfolio_history.append(snapshot)
        return snapshot


# ============================================================================
# RISK MANAGEMENT
# ============================================================================

class RiskManager:
    """Manages trading risk and position sizing"""
    
    def __init__(self, max_positions: int = 10, max_position_size_pct: float = 0.05, 
                 max_daily_loss_pct: float = 0.02, max_correlation: float = 0.7):
        self.max_positions = max_positions
        self.max_position_size_pct = max_position_size_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_correlation = max_correlation
    
    def calculate_position_size(self, portfolio_value: float, risk_amount: float, 
                               stop_loss_distance: float) -> float:
        """Calculate position size based on risk management"""
        
        if stop_loss_distance == 0:
            return 0
        
        # Risk-based position size
        position_size = risk_amount / stop_loss_distance
        
        # Cap position size to max % of portfolio
        max_size = portfolio_value * self.max_position_size_pct
        position_size = min(position_size, max_size)
        
        return position_size
    
    def can_open_position(self, portfolio: PortfolioManager, position_value: float) -> Tuple[bool, str]:
        """Check if new position can be opened"""
        
        # Check max positions
        if len(portfolio.positions) >= self.max_positions:
            return False, f"Max positions ({self.max_positions}) reached"
        
        # Check position size against portfolio
        max_position_value = portfolio.total_value * self.max_position_size_pct
        if position_value > max_position_value:
            return False, f"Position size exceeds max ({self.max_position_size_pct*100}%)"
        
        # Check available capital
        if position_value > portfolio.cash + portfolio.margin_available:
            return False, "Insufficient capital"
        
        return True, "OK"
    
    def check_daily_loss_limit(self, portfolio: PortfolioManager) -> bool:
        """Check if daily loss limit exceeded"""
        
        today_start_value = portfolio.initial_capital  # Simplified - in production use actual start-of-day
        daily_loss = portfolio.total_value - today_start_value
        daily_loss_pct = daily_loss / portfolio.initial_capital
        
        return daily_loss_pct >= -self.max_daily_loss_pct
    
    def validate_trade(self, portfolio: PortfolioManager, ticker: str, 
                      quantity: float, price: float, stop_loss: float) -> Tuple[bool, str]:
        """Validate trade before execution"""
        
        position_value = quantity * price
        stop_loss_distance = abs(price - stop_loss)
        
        # Check basic requirements
        if quantity <= 0:
            return False, "Invalid quantity"
        
        if price <= 0:
            return False, "Invalid price"
        
        if stop_loss <= 0:
            return False, "Invalid stop loss"
        
        # Check risk/reward
        if stop_loss_distance == 0:
            return False, "Stop loss too close to entry"
        
        # Check position viability
        can_open, reason = self.can_open_position(portfolio, position_value)
        if not can_open:
            return False, reason
        
        # Check daily loss limit
        if not self.check_daily_loss_limit(portfolio):
            return False, "Daily loss limit exceeded"
        
        return True, "OK"


# ============================================================================
# ORDER MANAGEMENT
# ============================================================================

class OrderManager:
    """Manages order placement and execution"""
    
    def __init__(self, portfolio: PortfolioManager):
        self.portfolio = portfolio
        self.order_queue: List[Order] = []
        self.filled_orders: List[Order] = []
        self.order_counter = 0
    
    def place_order(self, ticker: str, order_type: OrderType, side: OrderSide, 
                   quantity: float, price: float, stop_price: Optional[float] = None,
                   take_profit: Optional[float] = None, stop_loss: Optional[float] = None) -> Optional[Order]:
        """Place a new order"""
        
        order_id = f"ORD_{self.order_counter}_{ticker}"
        
        order = Order(
            order_id=order_id,
            ticker=ticker,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            stop_price=stop_price,
            take_profit=take_profit,
            stop_loss=stop_loss
        )
        
        self.order_queue.append(order)
        self.order_counter += 1
        
        _log_orders.info("Order placed  %s  %s  qty=%s  price=$%.2f  id=%s",
                         ticker, side.value, quantity, price, order_id)
        return order
    
    def execute_order(self, order: Order, execution_price: float) -> bool:
        """Execute an order at given price"""
        
        order.avg_filled_price = execution_price
        order.filled_quantity = order.quantity
        order.status = "FILLED"
        
        self.filled_orders.append(order)
        self.order_queue.remove(order)
        
        _log_orders.info("Order filled   %s  %s  qty=%s  price=$%.2f  id=%s",
                         order.ticker, order.side.value, order.quantity,
                         execution_price, order.order_id)
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        
        for order in self.order_queue:
            if order.order_id == order_id:
                order.status = "CANCELLED"
                self.order_queue.remove(order)
                _log_orders.info("Order cancelled  id=%s", order_id)
                return True
        
        return False
    
    def get_pending_orders(self, ticker: Optional[str] = None) -> List[Order]:
        """Get all pending orders, optionally filtered by ticker"""
        
        if ticker:
            return [o for o in self.order_queue if o.ticker == ticker]
        return self.order_queue.copy()


# ============================================================================
# TRADE LOGGER & ANALYSIS
# ============================================================================

class TradeLogger:
    """Logs and analyzes all trades"""
    
    def __init__(self, portfolio: PortfolioManager):
        self.portfolio = portfolio
    
    def get_trade_statistics(self) -> Dict:
        """Calculate trade statistics"""
        
        trades = self.portfolio.closed_positions
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'total_profit': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_holding_days': 0
            }
        
        df = pd.DataFrame([{
            'profit_loss': t.profit_loss,
            'return_pct': t.return_pct,
            'holding_days': t.holding_days,
            'win': t.win
        } for t in trades])
        
        winning = df[df['profit_loss'] > 0]
        losing = df[df['profit_loss'] < 0]
        
        profit_factor = winning['profit_loss'].sum() / abs(losing['profit_loss'].sum()) if len(losing) > 0 else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': len(winning) / len(trades) * 100 if len(trades) > 0 else 0,
            'profit_factor': profit_factor,
            'avg_win': winning['profit_loss'].mean() if len(winning) > 0 else 0,
            'avg_loss': losing['profit_loss'].mean() if len(losing) > 0 else 0,
            'total_profit': df['profit_loss'].sum(),
            'largest_win': df['profit_loss'].max(),
            'largest_loss': df['profit_loss'].min(),
            'avg_holding_days': df['holding_days'].mean() if len(trades) > 0 else 0
        }
    
    def print_trade_summary(self):
        """Print summary of all trades"""
        
        stats = self.get_trade_statistics()
        summary = self.portfolio.get_portfolio_summary()
        
        print("\n" + "="*70)
        print("TRADING SYSTEM SUMMARY")
        print("="*70)
        
        print(f"\nPORTFOLIO:")
        print(f"  Initial Capital:    ${summary['initial_capital']:>12,.2f}")
        print(f"  Total Value:        ${summary['total_value']:>12,.2f}")
        print(f"  Cash:               ${summary['cash']:>12,.2f}")
        print(f"  Return:             {summary['return_pct']:>12.2f}%")
        print(f"  Unrealized P&L:     ${summary['unrealized_pnl']:>12,.2f}")
        print(f"  Realized P&L:       ${summary['realized_pnl']:>12,.2f}")
        
        print(f"\nTRADES:")
        print(f"  Total Trades:       {stats['total_trades']:>12}")
        print(f"  Winning Trades:     {stats['winning_trades']:>12}")
        print(f"  Losing Trades:      {stats['losing_trades']:>12}")
        print(f"  Win Rate:           {stats['win_rate']:>12.2f}%")
        print(f"  Profit Factor:      {stats['profit_factor']:>12.2f}")
        
        print(f"\nTRADE ANALYSIS:")
        print(f"  Avg Win:            ${stats['avg_win']:>12,.2f}")
        print(f"  Avg Loss:           ${stats['avg_loss']:>12,.2f}")
        print(f"  Largest Win:        ${stats['largest_win']:>12,.2f}")
        print(f"  Largest Loss:       ${stats['largest_loss']:>12,.2f}")
        print(f"  Avg Holding Days:   {stats['avg_holding_days']:>12.1f}")
        
        print("\n" + "="*70)
        
        if stats['total_trades'] > 0:
            print(f"\nLAST 5 TRADES:")
            for i, trade in enumerate(self.portfolio.closed_positions[-5:], 1):
                win_loss = "WIN " if trade.win else "LOSS"
                print(f"  {i}. {trade.ticker} {trade.side:4s} {win_loss} | "
                      f"Entry: ${trade.entry_price:.2f} Exit: ${trade.exit_price:.2f} | "
                      f"P&L: ${trade.profit_loss:+.2f} ({trade.return_pct:+.2f}%)")


if __name__ == "__main__":
    print("Trading System Core Module - Ready for integration")
