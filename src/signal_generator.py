import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# ============================================================================
# SIGNAL STRUCTURES
# ============================================================================

@dataclass
class Signal:
    """Represents a trading signal"""
    ticker: str
    timestamp: datetime
    signal_type: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    strength: float  # Indicator of signal strength
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: List[str]  # List of indicators triggering signal
    timeframe: str = "daily"
    
    def __str__(self):
        emoji = "🔺" if self.signal_type == "BUY" else "🔻" if self.signal_type == "SELL" else "⚪"
        return f"{emoji} {self.signal_type} {self.ticker} @ ${self.entry_price:.2f} (Conf: {self.confidence:.1%})"


@dataclass
class IndicatorSnapshot:
    """Current values of all indicators"""
    timestamp: datetime
    close: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    adx: float
    plus_di: float
    minus_di: float
    atr: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    stoch_k: float
    stoch_d: float
    rsi_divergence: int  # -1, 0, 1


# ============================================================================
# SIGNAL GENERATOR
# ============================================================================

class SignalGenerator:
    """Generates trading signals based on technical analysis"""
    
    # Signal strength weights
    WEIGHTS = {
        'trend_alignment': 0.25,
        'momentum': 0.25,
        'reversal': 0.20,
        'volatility': 0.15,
        'volume': 0.15
    }
    
    def __init__(self, confidence_threshold: float = 0.55):
        self.confidence_threshold = confidence_threshold
        self.signal_history: List[Signal] = []
    
    def generate_signal(self, df: pd.DataFrame, current_row_idx: int, 
                       timeframe: str = "daily") -> Optional[Signal]:
        """Generate a signal based on current data"""
        
        if current_row_idx < 50:  # Need enough data for indicators
            return None
        
        row = df.iloc[current_row_idx]
        
        # Skip if indicators are NaN
        if pd.isna(row['RSI']) or pd.isna(row['ADX']) or pd.isna(row['MACD']):
            return None
        
        # Get indicator snapshot
        snap = IndicatorSnapshot(
            timestamp=row.name if isinstance(row.name, datetime) else datetime.now(),
            close=row['Close'],
            sma_20=row['SMA_20'],
            sma_50=row['SMA_50'],
            ema_12=row['EMA_12'],
            ema_26=row['EMA_26'],
            rsi=row['RSI'],
            macd=row['MACD'],
            macd_signal=row['MACD_Signal'],
            macd_histogram=row['MACD_Histogram'],
            adx=row['ADX'],
            plus_di=row['Plus_DI'],
            minus_di=row['Minus_DI'],
            atr=row['ATR'],
            bb_upper=row['BB_Upper'],
            bb_middle=row['BB_Middle'],
            bb_lower=row['BB_Lower'],
            stoch_k=row['Stoch_K'],
            stoch_d=row['Stoch_D'],
            rsi_divergence=int(row.get('RSI_Divergence', 0))
        )
        
        # Analyze for BUY signal
        buy_signal = self._analyze_buy_signal(snap, df, current_row_idx)
        if buy_signal:
            return buy_signal
        
        # Analyze for SELL signal
        sell_signal = self._analyze_sell_signal(snap, df, current_row_idx)
        if sell_signal:
            return sell_signal
        
        return None
    
    def _analyze_buy_signal(self, snap: IndicatorSnapshot, df: pd.DataFrame, 
                            row_idx: int) -> Optional[Signal]:
        """Analyze conditions for BUY signal"""
        
        reasons = []
        confidence_components = []
        
        # --- TREND ALIGNMENT (25%) ---
        trend_score = 0
        
        # Price above moving averages (bullish)
        if snap.close > snap.sma_20 and snap.sma_20 > snap.sma_50:
            reasons.append("✓ Price > SMA20 > SMA50")
            trend_score += 1.0
        elif snap.close > snap.sma_20:
            reasons.append("✓ Price > SMA20")
            trend_score += 0.5
        
        # EMA alignment
        if snap.ema_12 > snap.ema_26:
            reasons.append("✓ EMA12 > EMA26")
            trend_score += 0.5
        
        confidence_components.append(trend_score / 2.0 * self.WEIGHTS['trend_alignment'])
        
        # ---- MOMENTUM (25%) ----
        momentum_score = 0
        
        # MACD bullish
        if snap.macd > snap.macd_signal and snap.macd_histogram > 0:
            reasons.append("✓ MACD bullish crossover")
            momentum_score += 1.0
        
        # RSI in good zone (not overbought, not too low)
        if 40 < snap.rsi < 70:
            reasons.append(f"✓ RSI {snap.rsi:.1f} (bullish zone)")
            momentum_score += 0.8
        elif 30 < snap.rsi < 40:
            reasons.append(f"✓ RSI {snap.rsi:.1f} (recovery zone)")
            momentum_score += 0.5
        
        # Stochastic rising
        if snap.stoch_k > snap.stoch_d and snap.stoch_k < 80:
            reasons.append("✓ Stochastic rising")
            momentum_score += 0.5
        
        if momentum_score == 0:
            return None  # Require at least some momentum
        
        confidence_components.append(momentum_score / 2.5 * self.WEIGHTS['momentum'])
        
        # ---- REVERSAL (20%) ----
        reversal_score = 0
        
        # RSI divergence
        if snap.rsi_divergence == 1:
            reasons.append("✓ Bullish RSI divergence")
            reversal_score += 1.0
        
        # Price bouncing from support
        if snap.close > snap.bb_lower and snap.close < snap.bb_middle:
            reasons.append("✓ Price bouncing from lower BB")
            reversal_score += 0.7
        
        if reversal_score > 0:
            confidence_components.append(reversal_score / 1.7 * self.WEIGHTS['reversal'])
        else:
            confidence_components.append(0)
        
        # ---- TREND STRENGTH (15%) ----
        strength_score = 0
        
        # ADX trend strength
        if snap.adx > 25:
            reasons.append(f"✓ Strong trend (ADX {snap.adx:.1f})")
            strength_score += 1.0
        elif snap.adx > 20:
            reasons.append(f"✓ Trend exists (ADX {snap.adx:.1f})")
            strength_score += 0.7
        elif snap.adx < 15:
            return None  # No trend = no signal
        
        confidence_components.append(strength_score * self.WEIGHTS['volatility'])
        
        # ---- PRICE ACTION (15%) ----
        price_action_score = 0
        
        # Higher highs and higher lows
        if row_idx >= 2:
            prev_high = df['High'].iloc[row_idx - 1]
            prev_low = df['Low'].iloc[row_idx - 1]
            curr_high = df['High'].iloc[row_idx]
            curr_low = df['Low'].iloc[row_idx]
            
            if curr_high > prev_high and curr_low > prev_low:
                reasons.append("✓ Higher highs and lows")
                price_action_score += 1.0
        
        confidence_components.append(price_action_score * self.WEIGHTS['volume'])
        
        # ---- FINAL DECISION ----
        # Require minimum components to be positive
        if len(reasons) < 3:
            return None
        
        confidence = sum(confidence_components)
        
        if confidence >= self.confidence_threshold:
            # Calculate entry and stops
            entry_price = snap.close
            stop_loss = snap.close - (snap.atr * 2)
            take_profit = snap.close + (snap.atr * 3)
            
            signal = Signal(
                ticker="",  # Will be set by caller
                timestamp=snap.timestamp,
                signal_type="BUY",
                confidence=min(confidence, 1.0),
                strength=snap.adx,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reasons
            )
            
            return signal
        
        return None
    
    def _analyze_sell_signal(self, snap: IndicatorSnapshot, df: pd.DataFrame, 
                             row_idx: int) -> Optional[Signal]:
        """Analyze conditions for SELL signal"""
        
        reasons = []
        confidence_components = []
        
        # ---- TREND ALIGNMENT (25%) ----
        trend_score = 0
        
        # Price below moving averages (bearish)
        if snap.close < snap.sma_20 and snap.sma_20 < snap.sma_50:
            reasons.append("✓ Price < SMA20 < SMA50")
            trend_score += 1.0
        elif snap.close < snap.sma_20:
            reasons.append("✓ Price < SMA20")
            trend_score += 0.5
        
        # EMA alignment
        if snap.ema_12 < snap.ema_26:
            reasons.append("✓ EMA12 < EMA26")
            trend_score += 0.5
        
        confidence_components.append(trend_score / 2.0 * self.WEIGHTS['trend_alignment'])
        
        # ---- MOMENTUM (25%) ----
        momentum_score = 0
        
        # MACD bearish
        if snap.macd < snap.macd_signal and snap.macd_histogram < 0:
            reasons.append("✓ MACD bearish crossover")
            momentum_score += 1.0
        
        # RSI in good zone (not oversold, not too high)
        if 30 < snap.rsi < 60:
            reasons.append(f"✓ RSI {snap.rsi:.1f} (bearish zone)")
            momentum_score += 0.8
        elif 60 < snap.rsi < 70:
            reasons.append(f"✓ RSI {snap.rsi:.1f} (pullback zone)")
            momentum_score += 0.5
        
        # Stochastic falling
        if snap.stoch_k < snap.stoch_d and snap.stoch_k > 20:
            reasons.append("✓ Stochastic falling")
            momentum_score += 0.5
        
        if momentum_score == 0:
            return None
        
        confidence_components.append(momentum_score / 2.5 * self.WEIGHTS['momentum'])
        
        # ---- REVERSAL (20%) ----
        reversal_score = 0
        
        # RSI divergence
        if snap.rsi_divergence == -1:
            reasons.append("✓ Bearish RSI divergence")
            reversal_score += 1.0
        
        # Price bouncing from resistance
        if snap.close > snap.bb_middle and snap.close < snap.bb_upper:
            reasons.append("✓ Price bouncing from upper BB")
            reversal_score += 0.7
        
        if reversal_score > 0:
            confidence_components.append(reversal_score / 1.7 * self.WEIGHTS['reversal'])
        else:
            confidence_components.append(0)
        
        # ---- TREND STRENGTH (15%) ----
        strength_score = 0
        
        # ADX trend strength
        if snap.adx > 25:
            reasons.append(f"✓ Strong trend (ADX {snap.adx:.1f})")
            strength_score += 1.0
        elif snap.adx > 20:
            reasons.append(f"✓ Trend exists (ADX {snap.adx:.1f})")
            strength_score += 0.7
        elif snap.adx < 15:
            return None
        
        confidence_components.append(strength_score * self.WEIGHTS['volatility'])
        
        # ---- PRICE ACTION (15%) ----
        price_action_score = 0
        
        # Lower highs and lower lows
        if row_idx >= 2:
            prev_high = df['High'].iloc[row_idx - 1]
            prev_low = df['Low'].iloc[row_idx - 1]
            curr_high = df['High'].iloc[row_idx]
            curr_low = df['Low'].iloc[row_idx]
            
            if curr_high < prev_high and curr_low < prev_low:
                reasons.append("✓ Lower highs and lows")
                price_action_score += 1.0
        
        confidence_components.append(price_action_score * self.WEIGHTS['volume'])
        
        # ---- FINAL DECISION ----
        if len(reasons) < 3:
            return None
        
        confidence = sum(confidence_components)
        
        if confidence >= self.confidence_threshold:
            # Calculate entry and stops
            entry_price = snap.close
            stop_loss = snap.close + (snap.atr * 2)
            take_profit = snap.close - (snap.atr * 3)
            
            signal = Signal(
                ticker="",  # Will be set by caller
                timestamp=snap.timestamp,
                signal_type="SELL",
                confidence=min(confidence, 1.0),
                strength=snap.adx,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reasons
            )
            
            return signal
        
        return None
    
    def get_signal_summary(self) -> Dict:
        """Get summary of signals generated"""
        
        if not self.signal_history:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'avg_confidence': 0
            }
        
        buy_signals = [s for s in self.signal_history if s.signal_type == "BUY"]
        sell_signals = [s for s in self.signal_history if s.signal_type == "SELL"]
        
        return {
            'total_signals': len(self.signal_history),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'avg_confidence': np.mean([s.confidence for s in self.signal_history]) if self.signal_history else 0
        }


# ============================================================================
# MULTI-TIMEFRAME SIGNAL ANALYZER
# ============================================================================

class MultiTimeframeSignalAnalyzer:
    """Analyzes signals across multiple timeframes for confirmation"""
    
    def __init__(self):
        self.generators = {
            'weekly': SignalGenerator(),
            'daily': SignalGenerator(),
            '4h': SignalGenerator()
        }
    
    def get_confluence_score(self, signals: Dict[str, Optional[Signal]]) -> float:
        """Calculate signal confluence score (0-1)"""
        
        # Higher timeframes have more weight
        weights = {'weekly': 0.5, 'daily': 0.3, '4h': 0.2}
        
        score = 0
        count = 0
        
        for timeframe, signal in signals.items():
            if signal and signal.signal_type == "BUY":
                score += weights.get(timeframe, 0) * signal.confidence
                count += 1
        
        return min(score * 2, 1.0) if count > 0 else 0  # Normalize
    
    def analyze_confluence(self, signals: Dict[str, Optional[Signal]]) -> Tuple[str, float]:
        """Determine if signals show confluence (agreement across timeframes)"""
        
        buy_signals = [s for s in signals.values() if s and s.signal_type == "BUY"]
        sell_signals = [s for s in signals.values() if s and s.signal_type == "SELL"]
        
        # Check for agreement
        if len(buy_signals) >= 2:  # At least 2 timeframes bullish
            confidence = np.mean([s.confidence for s in buy_signals])
            return "BUY", confidence
        
        elif len(sell_signals) >= 2:  # At least 2 timeframes bearish
            confidence = np.mean([s.confidence for s in sell_signals])
            return "SELL", confidence
        
        else:
            return "HOLD", 0.0
    
    def get_combined_signal(self, signals: Dict[str, Optional[Signal]]) -> Optional[Signal]:
        """Create a combined signal from multiple timeframes"""
        
        signal_type, confidence = self.analyze_confluence(signals)
        
        if signal_type == "HOLD":
            return None
        
        # Use the strongest signal's parameters
        strongest = max(
            [s for s in signals.values() if s and s.signal_type == signal_type],
            key=lambda x: x.confidence,
            default=None
        )
        
        if not strongest:
            return None
        
        # Create combined signal
        combined = Signal(
            ticker=strongest.ticker,
            timestamp=datetime.now(),
            signal_type=signal_type,
            confidence=min(confidence, 1.0),
            strength=strongest.strength,
            entry_price=strongest.entry_price,
            stop_loss=strongest.stop_loss,
            take_profit=strongest.take_profit,
            reason=[f"Multi-TF confluence: {signal_type}", "Weekly + Daily aligned"],
            timeframe="multi"
        )
        
        return combined


if __name__ == "__main__":
    print("Signal Generation Engine - Ready for integration")
