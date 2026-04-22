"""Unit tests for PortfolioManager, RiskManager, OrderManager, TradeLogger."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.trading_system import (
    PortfolioManager, RiskManager, OrderManager, TradeLogger,
    OrderType, OrderSide,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def portfolio():
    return PortfolioManager(initial_capital=10000)

@pytest.fixture
def risk():
    return RiskManager(max_positions=5, max_position_size_pct=0.10)


# ── PortfolioManager ──────────────────────────────────────────────────────────

class TestPortfolioManager:
    def test_initial_state(self, portfolio):
        assert portfolio.total_value == 10000
        assert portfolio.cash == 10000
        assert len(portfolio.positions) == 0
        assert len(portfolio.closed_positions) == 0

    def test_open_position(self, portfolio):
        pos = portfolio.open_position(
            ticker="AAPL", entry_price=150.0, quantity=10,
            side="LONG", signal="test", stop_loss=145.0, take_profit=160.0,
        )
        assert pos is not None
        assert len(portfolio.positions) == 1
        assert portfolio.cash == pytest.approx(10000 - 150 * 10)

    def test_close_position(self, portfolio):
        pos = portfolio.open_position(
            ticker="AAPL", entry_price=150.0, quantity=10,
            side="LONG", signal="test", stop_loss=145.0, take_profit=160.0,
        )
        trade = portfolio.close_position(pos.position_id, exit_price=160.0)
        assert trade is not None
        assert trade.profit_loss == pytest.approx(100.0)
        assert len(portfolio.positions) == 0
        assert len(portfolio.closed_positions) == 1

    def test_close_long_loss(self, portfolio):
        pos = portfolio.open_position(
            ticker="AAPL", entry_price=150.0, quantity=10,
            side="LONG", signal="test", stop_loss=145.0, take_profit=160.0,
        )
        trade = portfolio.close_position(pos.position_id, exit_price=145.0)
        assert trade.profit_loss == pytest.approx(-50.0)
        assert not trade.win

    def test_close_short_win(self, portfolio):
        pos = portfolio.open_position(
            ticker="AAPL", entry_price=150.0, quantity=10,
            side="SHORT", signal="test", stop_loss=155.0, take_profit=140.0,
        )
        trade = portfolio.close_position(pos.position_id, exit_price=140.0)
        assert trade.profit_loss == pytest.approx(100.0)
        assert trade.win

    def test_get_portfolio_summary_keys(self, portfolio):
        summary = portfolio.get_portfolio_summary()
        for key in ("total_value", "cash", "return_pct", "open_positions", "realized_pnl"):
            assert key in summary


# ── RiskManager ───────────────────────────────────────────────────────────────

class TestRiskManager:
    def test_position_size_basic(self, risk):
        # $200 risk, $5 stop distance → 40 shares; capped at 10% of $10k = $1000
        size = risk.calculate_position_size(10000, 200, 5)
        assert size == pytest.approx(40.0)

    def test_position_size_zero_stop(self, risk):
        assert risk.calculate_position_size(10000, 200, 0) == 0

    def test_validate_trade_passes(self, portfolio, risk):
        valid, reason = risk.validate_trade(portfolio, "AAPL", quantity=5, price=100, stop_loss=95)
        assert valid, reason

    def test_validate_trade_exceeds_max_size(self, portfolio, risk):
        # quantity=200 * price=100 = $20,000 > 10% of $10,000
        valid, reason = risk.validate_trade(portfolio, "AAPL", quantity=200, price=100, stop_loss=95)
        assert not valid

    def test_validate_trade_insufficient_capital(self, portfolio, risk):
        valid, reason = risk.validate_trade(portfolio, "AAPL", quantity=1000, price=100, stop_loss=95)
        assert not valid

    def test_can_open_position_max_reached(self, portfolio, risk):
        risk.max_positions = 1
        portfolio.open_position("AAPL", 100, 5, "LONG", "s", 95, 110)
        can_open, msg = risk.can_open_position(portfolio, 500)
        assert not can_open

    def test_daily_loss_limit(self, portfolio, risk):
        # No losses yet → daily check should pass
        assert risk.check_daily_loss_limit(portfolio)


# ── OrderManager ─────────────────────────────────────────────────────────────

class TestOrderManager:
    def test_place_and_execute_market_order(self, portfolio):
        om = OrderManager(portfolio)
        order = om.place_order("AAPL", OrderType.MARKET, OrderSide.BUY, 10, 150.0)
        assert order is not None
        om.execute_order(order, 150.0)
        assert order.status == "FILLED"

    def test_cancel_order(self, portfolio):
        om = OrderManager(portfolio)
        order = om.place_order("AAPL", OrderType.LIMIT, OrderSide.BUY, 5, 100.0)
        om.cancel_order(order.order_id)
        assert order.status == "CANCELLED"


# ── TradeLogger ───────────────────────────────────────────────────────────────

class TestTradeLogger:
    def test_empty_stats(self, portfolio):
        logger = TradeLogger(portfolio)
        stats = logger.get_trade_statistics()
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0

    def test_stats_after_trades(self, portfolio):
        pos1 = portfolio.open_position("AAPL", 100, 10, "LONG", "s", 95, 110)
        portfolio.close_position(pos1.position_id, 110)
        pos2 = portfolio.open_position("AAPL", 100, 10, "LONG", "s", 95, 110)
        portfolio.close_position(pos2.position_id, 95)

        logger = TradeLogger(portfolio)
        stats = logger.get_trade_statistics()
        assert stats["total_trades"] == 2
        assert stats["winning_trades"] == 1
        assert stats["losing_trades"] == 1
        assert stats["win_rate"] == pytest.approx(50.0)
