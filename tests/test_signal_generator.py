"""Unit tests for SignalGenerator."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
import pandas as pd
from src.signal_generator import SignalGenerator, Signal
from src.indicator_calculator import IndicatorCalculator


def _bullish_df(n=100):
    """Synthetic uptrending DataFrame with all indicators calculated."""
    close = [100.0 + i * 0.5 for i in range(n)]
    df = pd.DataFrame({
        "Open":   [c - 0.2 for c in close],
        "High":   [c + 0.5 for c in close],
        "Low":    [c - 0.5 for c in close],
        "Close":  close,
        "Volume": [1_000_000] * n,
    })
    return IndicatorCalculator.calculate_all(df)


def _bearish_df(n=100):
    """Synthetic downtrending DataFrame."""
    close = [200.0 - i * 0.5 for i in range(n)]
    df = pd.DataFrame({
        "Open":   [c + 0.2 for c in close],
        "High":   [c + 0.5 for c in close],
        "Low":    [c - 0.5 for c in close],
        "Close":  close,
        "Volume": [1_000_000] * n,
    })
    return IndicatorCalculator.calculate_all(df)


class TestSignalGeneratorInit:
    def test_default_threshold(self):
        sg = SignalGenerator()
        assert sg.confidence_threshold == pytest.approx(0.55)

    def test_empty_history(self):
        sg = SignalGenerator()
        assert len(sg.signal_history) == 0


class TestSignalStructure:
    def test_signal_has_required_fields(self):
        from datetime import datetime
        s = Signal(
            ticker="AAPL",
            timestamp=datetime.now(),
            signal_type="BUY",
            confidence=0.75,
            strength=30,
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=160.0,
            reason=["Test reason"],
        )
        assert s.signal_type == "BUY"
        assert s.confidence == pytest.approx(0.75)
        assert s.stop_loss < s.entry_price
        assert s.take_profit > s.entry_price


class TestGenerateSignal:
    def test_returns_none_before_warmup(self):
        sg = SignalGenerator()
        df = _bullish_df(100)
        # Index 10 is before warmup (needs ~50 bars)
        result = sg.generate_signal(df, 10, "daily")
        assert result is None

    def test_signal_type_is_buy_or_sell(self):
        sg = SignalGenerator()
        df = _bullish_df(100)
        for idx in range(60, 100):
            result = sg.generate_signal(df, idx, "daily")
            if result is not None:
                assert result.signal_type in ("BUY", "SELL")
                break

    def test_confidence_above_threshold(self):
        sg = SignalGenerator()
        df = _bullish_df(100)
        for idx in range(60, 100):
            result = sg.generate_signal(df, idx, "daily")
            if result is not None:
                assert result.confidence >= sg.confidence_threshold
                break

    def test_stop_loss_below_entry_for_buy(self):
        sg = SignalGenerator()
        df = _bullish_df(100)
        for idx in range(60, 100):
            result = sg.generate_signal(df, idx, "daily")
            if result is not None and result.signal_type == "BUY":
                assert result.stop_loss < result.entry_price
                assert result.take_profit > result.entry_price
                break

    def test_stop_loss_above_entry_for_sell(self):
        sg = SignalGenerator()
        df = _bearish_df(100)
        for idx in range(60, 100):
            result = sg.generate_signal(df, idx, "daily")
            if result is not None and result.signal_type == "SELL":
                assert result.stop_loss > result.entry_price
                assert result.take_profit < result.entry_price
                break


class TestGetSignalSummary:
    def test_empty_summary(self):
        sg = SignalGenerator()
        s = sg.get_signal_summary()
        assert s["total_signals"] == 0
        assert s["avg_confidence"] == 0

    def test_summary_after_signals(self):
        sg = SignalGenerator()
        df = _bullish_df(100)
        for idx in range(55, 100):
            sg.generate_signal(df, idx, "daily")
        s = sg.get_signal_summary()
        assert s["total_signals"] == s["buy_signals"] + s["sell_signals"]
        if s["total_signals"] > 0:
            assert 0.55 <= s["avg_confidence"] <= 1.0
