"""Integration tests: full open → execute → close cycle through AutomatedTradingSystem."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from datetime import datetime, timedelta

from src.automated_trading_system import AutomatedTradingSystem
from src.signal_generator import Signal


def _mock_download(ticker, start, end, progress=False):
    """Return a synthetic daily OHLCV DataFrame (no network call)."""
    dates = pd.date_range(start=start, end=end, freq="B")
    n = len(dates)
    np.random.seed(42)
    close = 150.0 + np.cumsum(np.random.randn(n) * 0.5)
    close = np.clip(close, 50, 500)
    df = pd.DataFrame({
        "Open":   close - 0.5,
        "High":   close + 1.0,
        "Low":    close - 1.0,
        "Close":  close,
        "Volume": np.random.randint(500_000, 5_000_000, n),
    }, index=dates)
    return df


@pytest.fixture
def system():
    return AutomatedTradingSystem(
        initial_capital=10000,
        ticker="AAPL",
        max_positions=5,
        max_position_size_pct=0.05,
    )


class TestBacktestIntegration:
    def test_backtest_returns_dict(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            results = system.backtest("2023-01-01", "2024-01-01")
        assert isinstance(results, dict)
        assert "portfolio" in results
        assert "trades" in results
        assert "signals" in results

    def test_portfolio_value_positive(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            system.backtest("2023-01-01", "2024-01-01")
        assert system.portfolio.total_value > 0

    def test_indicators_populated(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            system.fetch_data("2023-01-01", "2024-01-01")
            system.calculate_indicators()
        assert "daily" in system.indicators
        df = system.indicators["daily"]
        assert "RSI" in df.columns
        assert "MACD" in df.columns
        assert "ADX" in df.columns

    def test_no_position_after_full_backtest(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            system.backtest("2023-01-01", "2024-01-01")
        assert not system.in_position


class TestManualSignalExecution:
    def test_execute_buy_signal_opens_position(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            system.fetch_data("2023-01-01", "2024-01-01")

        signal = Signal(
            ticker="AAPL",
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=0.80,
            strength=30,
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=162.0,
            reason=["Test"],
        )
        executed = system.execute_signal(signal)
        assert executed
        assert system.in_position
        assert len(system.portfolio.positions) == 1

    def test_execute_signal_respects_position_limit(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            system.fetch_data("2023-01-01", "2024-01-01")

        system.risk_manager.max_positions = 1

        def _make_signal(price):
            return Signal(
                ticker="AAPL", timestamp=datetime.now(),
                signal_type="BUY", confidence=0.80, strength=30,
                entry_price=price, stop_loss=price * 0.97, take_profit=price * 1.08,
                reason=["Test"],
            )

        system.execute_signal(_make_signal(150.0))
        # Second signal should be rejected (already in position / max_positions=1)
        second = system.execute_signal(_make_signal(155.0))
        assert len(system.portfolio.positions) == 1


class TestFetchDataIntegration:
    def test_fetch_data_populates_timeframes(self, system):
        with patch("yfinance.download", side_effect=_mock_download):
            ok = system.fetch_data("2023-01-01", "2024-01-01")
        assert ok
        assert "daily" in system.data
        assert "weekly" in system.data
        assert not system.data["daily"].empty

    def test_fetch_data_returns_false_on_empty(self, system):
        # Patch both yfinance and the cache-file existence check so the empty
        # DataFrame propagates all the way through fetch_data.
        with patch("yfinance.download", return_value=pd.DataFrame()), \
             patch("src.automated_trading_system.os.path.exists", return_value=False):
            ok = system.fetch_data("2023-01-01", "2024-01-01")
        assert not ok
