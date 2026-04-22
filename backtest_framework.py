import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class TechnicalIndicators:
    """Calculate technical indicators for stock trend prediction"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range - measures volatility"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index - measures trend strength"""
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
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=3).mean()
        return k, d
    
    @staticmethod
    def rsi_divergence(rsi: pd.Series, price: pd.Series, window: int = 14) -> pd.Series:
        """Detect RSI divergences - bullish/bearish signals"""
        divergence = pd.Series(0, index=rsi.index)
        
        for i in range(window, len(rsi) - window):
            # Bullish divergence: lower low in price, higher low in RSI
            if (price.iloc[i-window:i].min() < price.iloc[i-window*2:i-window].min() and 
                rsi.iloc[i-window:i].min() > rsi.iloc[i-window*2:i-window].min()):
                divergence.iloc[i] = 1
            
            # Bearish divergence: higher high in price, lower high in RSI
            elif (price.iloc[i-window:i].max() > price.iloc[i-window*2:i-window].max() and 
                  rsi.iloc[i-window:i].max() < rsi.iloc[i-window*2:i-window].max()):
                divergence.iloc[i] = -1
        
        return divergence


class MultiTimeframeAnalyzer:
    """Analyze multiple timeframes for trend prediction"""
    
    def __init__(self, ticker: str, start_date: str, end_date: str):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data = {}
        self.indicators = {}
        
    def fetch_data(self):
        """Fetch historical data from Yahoo Finance"""
        try:
            print(f"Fetching data for {self.ticker}...")
            full_data = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
            if isinstance(full_data.columns, pd.MultiIndex):
                full_data.columns = full_data.columns.get_level_values(0)

            # Create different timeframes
            self.data['daily'] = full_data.copy()
            self.data['weekly'] = full_data.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            self.data['4h'] = full_data.resample('4h').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            
            print(f"✓ Data loaded: {len(self.data['daily'])} daily bars")
            return True
        except Exception as e:
            print(f"✗ Error fetching data: {e}")
            return False
    
    def calculate_indicators(self, timeframe: str = 'daily'):
        """Calculate all technical indicators for a timeframe"""
        if timeframe not in self.data:
            print(f"✗ Timeframe {timeframe} not found")
            return False
        
        df = self.data[timeframe].copy()
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        print(f"Calculating indicators for {timeframe}...")
        
        # Trend indicators
        df['SMA_20'] = TechnicalIndicators.sma(close, 20)
        df['SMA_50'] = TechnicalIndicators.sma(close, 50)
        df['EMA_12'] = TechnicalIndicators.ema(close, 12)
        df['EMA_26'] = TechnicalIndicators.ema(close, 26)
        
        # Momentum indicators
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = TechnicalIndicators.macd(close)
        df['RSI'] = TechnicalIndicators.rsi(close, 14)
        df['RSI_Divergence'] = TechnicalIndicators.rsi_divergence(df['RSI'], close)
        
        # Volatility indicators
        df['ATR'] = TechnicalIndicators.atr(high, low, close, 14)
        df['ADX'], df['Plus_DI'], df['Minus_DI'] = TechnicalIndicators.adx(high, low, close, 14)
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = TechnicalIndicators.bollinger_bands(close, 20, 2)
        
        # Stochastic
        df['Stoch_K'], df['Stoch_D'] = TechnicalIndicators.stochastic(high, low, close, 14)
        
        # Price action
        df['Higher_High'] = (high > high.shift(1)).astype(int)
        df['Higher_Low'] = (low > low.shift(1)).astype(int)
        df['Lower_High'] = (high < high.shift(1)).astype(int)
        df['Lower_Low'] = (low < low.shift(1)).astype(int)
        
        self.indicators[timeframe] = df
        print(f"✓ Indicators calculated for {timeframe}")
        return True
    
    def generate_signals(self, timeframe: str = 'daily') -> pd.DataFrame:
        """Generate trading signals based on technical analysis"""
        if timeframe not in self.indicators:
            print(f"✗ Indicators not calculated for {timeframe}")
            return None
        
        df = self.indicators[timeframe].copy()
        
        # Signal: 1 = Bullish, -1 = Bearish, 0 = Neutral
        df['Signal'] = 0
        
        # Trend confirmation (multiple indicators must align)
        bullish_conditions = (
            (df['Close'] > df['SMA_20']) &  # Price above 20-SMA
            (df['SMA_20'] > df['SMA_50']) &  # 20-SMA above 50-SMA
            (df['MACD'] > df['MACD_Signal']) &  # MACD bullish
            (df['RSI'] > 40) & (df['RSI'] < 70) &  # RSI in bullish zone
            (df['ADX'] > 20)  # Trend exists
        )
        
        bearish_conditions = (
            (df['Close'] < df['SMA_20']) &  # Price below 20-SMA
            (df['SMA_20'] < df['SMA_50']) &  # 20-SMA below 50-SMA
            (df['MACD'] < df['MACD_Signal']) &  # MACD bearish
            (df['RSI'] < 60) & (df['RSI'] > 30) &  # RSI in bearish zone
            (df['ADX'] > 20)  # Trend exists
        )
        
        df.loc[bullish_conditions, 'Signal'] = 1
        df.loc[bearish_conditions, 'Signal'] = -1
        
        # Reversal signals (RSI divergence)
        df.loc[(df['RSI_Divergence'] == 1), 'Signal'] = 1
        df.loc[(df['RSI_Divergence'] == -1), 'Signal'] = -1
        
        return df
    
    def analyze_all_timeframes(self) -> Dict[str, pd.DataFrame]:
        """Analyze all timeframes and return signals"""
        results = {}
        for timeframe in ['weekly', 'daily', '4h']:
            if timeframe in self.data:
                self.calculate_indicators(timeframe)
                signals = self.generate_signals(timeframe)
                results[timeframe] = signals
        
        return results


class BacktestEngine:
    """Backtest trading strategy across multiple timeframes"""
    
    def __init__(self, initial_capital: float = 10000, risk_per_trade: float = 0.02):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.trades = []
        self.equity_curve = []
        
    def backtest(self, signals_df: pd.DataFrame, timeframe: str = 'daily') -> Dict:
        """Run backtest on signal data"""
        df = signals_df.copy()
        
        # Position tracking
        position = 0
        entry_price = 0
        entry_signal = 0
        cash = self.initial_capital
        portfolio_value = self.initial_capital
        
        for idx in range(len(df)):
            current_price = df['Close'].iloc[idx]
            signal = df['Signal'].iloc[idx]
            atr = df['ATR'].iloc[idx]
            
            # Skip if not enough data
            if pd.isna(signal) or pd.isna(atr):
                continue
            
            # Entry signals
            if position == 0 and signal != 0:
                # Calculate position size based on risk
                stop_loss = atr * 2  # 2x ATR stop loss
                risk_amount = portfolio_value * self.risk_per_trade
                position_size = risk_amount / stop_loss if stop_loss > 0 else 0
                
                if position_size > 0:
                    position = position_size * signal  # Positive for long, negative for short
                    entry_price = current_price
                    entry_signal = signal
                    cash -= abs(position) * current_price
            
            # Exit signals
            elif position != 0:
                # Take profit: RSI extreme
                tp_condition = (entry_signal == 1 and df['RSI'].iloc[idx] > 70) or \
                              (entry_signal == -1 and df['RSI'].iloc[idx] < 30)
                
                # Stop loss: MACD histogram reverses
                sl_condition = (entry_signal == 1 and df['MACD_Histogram'].iloc[idx] < 0) or \
                              (entry_signal == -1 and df['MACD_Histogram'].iloc[idx] > 0)
                
                if tp_condition or sl_condition:
                    exit_price = current_price
                    profit_loss = (exit_price - entry_price) * position
                    cash += abs(position) * exit_price
                    
                    self.trades.append({
                        'entry_date': df.index[idx - 5] if idx >= 5 else df.index[0],
                        'exit_date': df.index[idx],
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position_size': position,
                        'profit_loss': profit_loss,
                        'return_pct': (exit_price - entry_price) / entry_price * 100 * np.sign(position),
                        'type': 'TP' if tp_condition else 'SL'
                    })
                    
                    position = 0
                    entry_price = 0
            
            # Update portfolio value
            if position != 0:
                portfolio_value = cash + abs(position) * current_price
            else:
                portfolio_value = cash
            
            self.equity_curve.append(portfolio_value)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        return metrics
    
    def _calculate_metrics(self) -> Dict:
        """Calculate backtest performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'return_pct': 0,
                'sharpe_ratio': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        winning_trades = trades_df[trades_df['profit_loss'] > 0]['profit_loss'].sum()
        losing_trades = abs(trades_df[trades_df['profit_loss'] < 0]['profit_loss'].sum())
        
        metrics = {
            'total_trades': len(trades_df),
            'winning_trades': len(trades_df[trades_df['profit_loss'] > 0]),
            'losing_trades': len(trades_df[trades_df['profit_loss'] < 0]),
            'win_rate': len(trades_df[trades_df['profit_loss'] > 0]) / len(trades_df) * 100,
            'profit_factor': winning_trades / losing_trades if losing_trades > 0 else 0,
            'total_profit': trades_df['profit_loss'].sum(),
            'avg_trade': trades_df['profit_loss'].mean(),
            'max_drawdown': self._calculate_max_drawdown(),
            'return_pct': (self.equity_curve[-1] - self.initial_capital) / self.initial_capital * 100 if self.equity_curve else 0,
            'sharpe_ratio': self._calculate_sharpe_ratio()
        }
        
        return metrics
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if not self.equity_curve:
            return 0
        
        cummax = np.maximum.accumulate(self.equity_curve)
        drawdown = (np.array(self.equity_curve) - cummax) / cummax
        return min(drawdown) * 100
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio"""
        if len(self.equity_curve) < 2:
            return 0
        
        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
        excess_returns = returns - risk_free_rate / 252
        
        if np.std(excess_returns) == 0:
            return 0
        
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)


def run_analysis(ticker: str, start_date: str, end_date: str):
    """Run complete multi-timeframe analysis and backtest"""
    
    # Initialize analyzer
    analyzer = MultiTimeframeAnalyzer(ticker, start_date, end_date)
    
    # Fetch data
    if not analyzer.fetch_data():
        return
    
    # Analyze all timeframes
    print("\n" + "="*60)
    print("MULTI-TIMEFRAME ANALYSIS")
    print("="*60)
    
    all_signals = analyzer.analyze_all_timeframes()
    
    # Display latest signals
    for timeframe, signals_df in all_signals.items():
        latest = signals_df.iloc[-1]
        signal_text = "🔺 BULLISH" if latest['Signal'] == 1 else "🔻 BEARISH" if latest['Signal'] == -1 else "⚪ NEUTRAL"
        
        print(f"\n{timeframe.upper()}:")
        print(f"  Signal: {signal_text}")
        print(f"  Price: ${latest['Close']:.2f}")
        print(f"  SMA_20: ${latest['SMA_20']:.2f} | SMA_50: ${latest['SMA_50']:.2f}")
        print(f"  RSI: {latest['RSI']:.2f} | ADX: {latest['ADX']:.2f} | ATR: ${latest['ATR']:.2f}")
        print(f"  MACD: {latest['MACD']:.4f} | Signal: {latest['MACD_Signal']:.4f}")
    
    # Backtest on daily timeframe
    print("\n" + "="*60)
    print("BACKTEST RESULTS (DAILY)")
    print("="*60)
    
    backtest = BacktestEngine(initial_capital=10000, risk_per_trade=0.02)
    metrics = backtest.backtest(all_signals['daily'], 'daily')
    
    print(f"\nTotal Trades: {metrics['total_trades']}")
    print(f"Winning Trades: {metrics['winning_trades']} | Losing Trades: {metrics['losing_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Total Profit: ${metrics['total_profit']:.2f}")
    print(f"Avg Trade: ${metrics['avg_trade']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Return: {metrics['return_pct']:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    return analyzer, all_signals, backtest


# Example usage
if __name__ == "__main__":
    ticker = "AAPL"  # Change to your ticker
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    
    run_analysis(ticker, start_date, end_date)
