"""Unit tests for IndicatorCalculator."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
import pandas as pd
from src.indicator_calculator import IndicatorCalculator


def _series(values):
    return pd.Series(values, dtype=float)


def _ohlcv(n=100, start=100.0, drift=0.1):
    """Synthetic OHLCV DataFrame with gentle uptrend."""
    close = [start + i * drift for i in range(n)]
    df = pd.DataFrame({
        "Open":  [c - 0.5 for c in close],
        "High":  [c + 1.0 for c in close],
        "Low":   [c - 1.0 for c in close],
        "Close": close,
        "Volume": [1_000_000] * n,
    })
    return df


class TestSMA:
    def test_constant_series(self):
        s = _series([5.0] * 30)
        result = IndicatorCalculator.sma(s, 10)
        assert result.dropna().iloc[-1] == pytest.approx(5.0)

    def test_period_1_equals_input(self):
        s = _series([1.0, 2.0, 3.0])
        result = IndicatorCalculator.sma(s, 1)
        pd.testing.assert_series_equal(result, s)

    def test_warmup_nan(self):
        s = _series(list(range(20)))
        result = IndicatorCalculator.sma(s, 10)
        assert result.iloc[:9].isna().all()
        assert not pd.isna(result.iloc[9])


class TestEMA:
    def test_constant_series(self):
        s = _series([3.0] * 30)
        result = IndicatorCalculator.ema(s, 10)
        assert result.iloc[-1] == pytest.approx(3.0, abs=1e-6)

    def test_output_length(self):
        s = _series(range(50))
        assert len(IndicatorCalculator.ema(s, 12)) == 50


class TestMACD:
    def test_returns_three_series(self):
        s = _series([float(i) for i in range(60)])
        macd, signal, hist = IndicatorCalculator.macd(s)
        assert len(macd) == len(signal) == len(hist) == 60

    def test_histogram_is_macd_minus_signal(self):
        s = _series([float(i) + (i % 3) for i in range(60)])
        macd, signal, hist = IndicatorCalculator.macd(s)
        expected = macd - signal
        pd.testing.assert_series_equal(hist, expected)


class TestRSI:
    def test_range(self):
        df = _ohlcv(100)
        rsi = IndicatorCalculator.rsi(df["Close"], 14)
        valid = rsi.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_constant_series_edge(self):
        s = _series([50.0] * 30)
        rsi = IndicatorCalculator.rsi(s, 14)
        # All gains and losses are zero → RSI is NaN or neutral
        valid = rsi.dropna()
        assert len(valid) == 0 or valid.between(0, 100).all()


class TestATR:
    def test_positive(self):
        df = _ohlcv(50)
        atr = IndicatorCalculator.atr(df["High"], df["Low"], df["Close"], 14)
        assert (atr.dropna() > 0).all()

    def test_output_length(self):
        df = _ohlcv(50)
        atr = IndicatorCalculator.atr(df["High"], df["Low"], df["Close"], 14)
        assert len(atr) == 50


class TestADX:
    def test_returns_three_series(self):
        df = _ohlcv(80)
        adx, plus_di, minus_di = IndicatorCalculator.adx(
            df["High"], df["Low"], df["Close"], 14)
        assert len(adx) == len(plus_di) == len(minus_di) == 80

    def test_adx_non_negative(self):
        df = _ohlcv(80)
        adx, _, _ = IndicatorCalculator.adx(df["High"], df["Low"], df["Close"], 14)
        assert (adx.dropna() >= 0).all()


class TestBollingerBands:
    def test_upper_above_lower(self):
        df = _ohlcv(60)
        upper, mid, lower = IndicatorCalculator.bollinger_bands(df["Close"], 20, 2)
        valid = upper.dropna()
        assert (upper.dropna() > lower.dropna()).all()

    def test_mid_is_sma(self):
        df = _ohlcv(60)
        _, mid, _ = IndicatorCalculator.bollinger_bands(df["Close"], 20, 2)
        sma = IndicatorCalculator.sma(df["Close"], 20)
        pd.testing.assert_series_equal(mid, sma)


class TestStochastic:
    def test_range(self):
        df = _ohlcv(60)
        k, d = IndicatorCalculator.stochastic(df["High"], df["Low"], df["Close"], 14)
        valid_k = k.dropna()
        assert (valid_k >= 0).all() and (valid_k <= 100).all()

    def test_d_is_smoothed_k(self):
        df = _ohlcv(60)
        k, d = IndicatorCalculator.stochastic(df["High"], df["Low"], df["Close"], 14)
        expected_d = k.rolling(3).mean()
        pd.testing.assert_series_equal(d, expected_d)


class TestCalculateAll:
    def test_all_columns_present(self):
        df = _ohlcv(100)
        result = IndicatorCalculator.calculate_all(df.copy())
        expected_cols = [
            "SMA_20", "SMA_50", "SMA_200", "EMA_12", "EMA_26",
            "MACD", "MACD_Signal", "MACD_Histogram", "RSI", "RSI_Divergence",
            "ATR", "ADX", "Plus_DI", "Minus_DI",
            "BB_Upper", "BB_Middle", "BB_Lower",
            "Stoch_K", "Stoch_D",
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"
