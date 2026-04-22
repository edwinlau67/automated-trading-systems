import pandas as pd
import numpy as np
from typing import Tuple


class IndicatorCalculator:
    """Calculate all technical indicators for a price DataFrame."""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        close = df['Close']
        high  = df['High']
        low   = df['Low']

        df['SMA_20']  = IndicatorCalculator.sma(close, 20)
        df['SMA_50']  = IndicatorCalculator.sma(close, 50)
        df['SMA_200'] = IndicatorCalculator.sma(close, 200)
        df['EMA_12']  = IndicatorCalculator.ema(close, 12)
        df['EMA_26']  = IndicatorCalculator.ema(close, 26)

        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = IndicatorCalculator.macd(close)
        df['RSI']           = IndicatorCalculator.rsi(close, 14)
        df['RSI_Divergence'] = IndicatorCalculator.rsi_divergence(df['RSI'], close)

        df['ATR']                             = IndicatorCalculator.atr(high, low, close, 14)
        df['ADX'], df['Plus_DI'], df['Minus_DI'] = IndicatorCalculator.adx(high, low, close, 14)
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = IndicatorCalculator.bollinger_bands(close, 20, 2)

        df['Stoch_K'], df['Stoch_D'] = IndicatorCalculator.stochastic(high, low, close, 14)

        return df

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26,
             signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast   = data.ewm(span=fast,   adjust=False).mean()
        ema_slow   = data.ewm(span=slow,   adjust=False).mean()
        macd_line  = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram  = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain  = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss  = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs    = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def rsi_divergence(rsi: pd.Series, price: pd.Series, window: int = 14) -> pd.Series:
        divergence = pd.Series(0, index=rsi.index)
        for i in range(window * 2, len(rsi)):
            price_prev = price.iloc[i - window * 2 : i - window]
            price_curr = price.iloc[i - window : i]
            rsi_prev   = rsi.iloc[i - window * 2 : i - window]
            rsi_curr   = rsi.iloc[i - window : i]
            if price_curr.min() < price_prev.min() and rsi_curr.min() > rsi_prev.min():
                divergence.iloc[i] = 1   # bullish
            elif price_curr.max() > price_prev.max() and rsi_curr.max() < rsi_prev.max():
                divergence.iloc[i] = -1  # bearish
        return divergence

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series,
            period: int = 14) -> pd.Series:
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series,
            period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        plus_dm  = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)

        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)

        atr      = tr.rolling(window=period).mean()
        plus_di  = 100 * (plus_dm.rolling(window=period).mean()  / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx  = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        return adx, plus_di, minus_di

    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20,
                        std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        sma   = data.rolling(window=period).mean()
        std   = data.rolling(window=period).std()
        upper = sma + std * std_dev
        lower = sma - std * std_dev
        return upper, sma, lower

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                   period: int = 14) -> Tuple[pd.Series, pd.Series]:
        lowest_low   = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=3).mean()
        return k, d
