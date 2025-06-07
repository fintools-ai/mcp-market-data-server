from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap with all relevant data"""
    gap_id: str
    gap_type: str  # 'bullish' or 'bearish'
    timeframe: str
    timestamp: datetime
    gap_high: float
    gap_low: float
    gap_size: float
    gap_midpoint: float
    candle_data: Dict[str, Dict[str, float]]
    volume_data: Dict[str, float]
    age_minutes: int
    times_tested: int = 0
    lowest_test: Optional[float] = None
    highest_test: Optional[float] = None
    filled_percentage: float = 0.0
    currently_inside_gap: bool = False


class FVGCalculator:
    """Calculates Fair Value Gaps from OHLCV data"""
    
    def __init__(self, min_gap_percentage: float = 0.1):
        """
        Initialize FVG Calculator
        
        Args:
            min_gap_percentage: Minimum gap size as percentage of price (default: 0.1%)
        """
        self.min_gap_percentage = min_gap_percentage
    
    def detect_fvgs(self, 
                    df: pd.DataFrame, 
                    timeframe: str,
                    current_price: float,
                    lookback_periods: int = 100) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps in price data
        
        Args:
            df: DataFrame with OHLCV data (newest first)
            timeframe: Timeframe string (e.g., '1m', '5m')
            current_price: Current market price
            lookback_periods: Number of periods to analyze
            
        Returns:
            List of FairValueGap objects
        """
        if df is None or len(df) < 3:
            return []
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            return []
        
        # Limit lookback (get most recent data since df is chronological)
        df_analysis = df.tail(min(lookback_periods, len(df)))
        
        gaps = []
        current_time = datetime.now()
        
        # Scan for 3-candle patterns (from most recent backwards)
        for i in range(len(df_analysis) - 1, 1, -1):
            # Get three consecutive candles (working backwards from most recent)
            candle3 = df_analysis.iloc[i]      # Most recent of the three
            candle2 = df_analysis.iloc[i - 1]  # Middle
            candle1 = df_analysis.iloc[i - 2]  # Oldest of the three
            
            # Check for bullish FVG: candle1.high < candle3.low
            if candle1['high'] < candle3['low']:
                gap_low = candle1['high']
                gap_high = candle3['low']
                gap_type = 'bullish'
                
            # Check for bearish FVG: candle1.low > candle3.high
            elif candle1['low'] > candle3['high']:
                gap_high = candle1['low']
                gap_low = candle3['high']
                gap_type = 'bearish'
                
            else:
                continue  # No gap
            
            # Calculate gap metrics
            gap_size = gap_high - gap_low
            gap_midpoint = (gap_high + gap_low) / 2
            gap_percentage = (gap_size / gap_midpoint) * 100
            
            # Skip if gap is too small
            if gap_percentage < self.min_gap_percentage:
                continue
            
            # Create timestamp (if datetime column exists)
            if 'datetime' in df_analysis.columns:
                gap_timestamp = df_analysis.iloc[i]['datetime']
            else:
                gap_timestamp = df_analysis.index[i] if isinstance(df_analysis.index, pd.DatetimeIndex) else current_time
            
            # Calculate age
            if isinstance(gap_timestamp, pd.Timestamp):
                age_minutes = int((current_time - gap_timestamp.to_pydatetime()).total_seconds() / 60)
            else:
                age_minutes = i  # Use candle count as proxy
            
            # Create gap ID
            gap_id = f"{timeframe}_{gap_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ') if isinstance(gap_timestamp, pd.Timestamp) else f'gap_{i}'}"
            
            # Prepare candle data
            candle_data = {
                'candle_1': {
                    'high': float(candle1['high']),
                    'low': float(candle1['low']),
                    'close': float(candle1['close'])
                },
                'candle_2': {
                    'high': float(candle2['high']),
                    'low': float(candle2['low']),
                    'close': float(candle2['close'])
                },
                'candle_3': {
                    'high': float(candle3['high']),
                    'low': float(candle3['low']),
                    'close': float(candle3['close'])
                }
            }
            
            # Volume analysis
            avg_volume_20 = df_analysis['volume'].head(20).mean() if len(df_analysis) >= 20 else df_analysis['volume'].mean()
            volume_data = {
                'candle_1_volume': float(candle1['volume']),
                'candle_2_volume': float(candle2['volume']),
                'candle_3_volume': float(candle3['volume']),
                'avg_volume_20_periods': float(avg_volume_20)
            }
            
            # Create FVG object
            fvg = FairValueGap(
                gap_id=gap_id,
                gap_type=gap_type,
                timeframe=timeframe,
                timestamp=gap_timestamp,
                gap_high=float(gap_high),
                gap_low=float(gap_low),
                gap_size=float(gap_size),
                gap_midpoint=float(gap_midpoint),
                candle_data=candle_data,
                volume_data=volume_data,
                age_minutes=age_minutes
            )
            
            # Analyze interaction with current price and historical prices (candles after the gap)
            self._analyze_gap_interaction(fvg, df_analysis.iloc[i+1:], current_price)
            
            gaps.append(fvg)
        
        return gaps
    
    def _analyze_gap_interaction(self, fvg: FairValueGap, price_history: pd.DataFrame, current_price: float):
        """
        Analyze how price has interacted with the gap
        
        Args:
            fvg: FairValueGap object to analyze
            price_history: Price data after gap formation
            current_price: Current market price
        """
        if price_history.empty:
            return
        
        # Check if current price is inside gap
        fvg.currently_inside_gap = fvg.gap_low <= current_price <= fvg.gap_high
        
        # Count tests and track extremes
        tests = 0
        lowest_test = None
        highest_test = None
        
        for _, candle in price_history.iterrows():
            candle_high = candle['high']
            candle_low = candle['low']
            
            # Check if candle tested the gap
            if (candle_low <= fvg.gap_high and candle_high >= fvg.gap_low):
                tests += 1
                
                # Track test extremes within gap boundaries
                test_low = max(candle_low, fvg.gap_low)
                test_high = min(candle_high, fvg.gap_high)
                
                if lowest_test is None or test_low < lowest_test:
                    lowest_test = test_low
                if highest_test is None or test_high > highest_test:
                    highest_test = test_high
        
        fvg.times_tested = tests
        fvg.lowest_test = float(lowest_test) if lowest_test is not None else None
        fvg.highest_test = float(highest_test) if highest_test is not None else None
        
        # Calculate fill percentage
        if fvg.times_tested > 0 and lowest_test is not None and highest_test is not None:
            filled_range = highest_test - lowest_test
            fvg.filled_percentage = min((filled_range / fvg.gap_size) * 100, 100.0)
    
    def calculate_gap_statistics(self, gaps: List[FairValueGap], timeframe: str) -> Dict[str, Any]:
        """
        Calculate statistics for a list of gaps
        
        Args:
            gaps: List of FairValueGap objects
            timeframe: Timeframe string
            
        Returns:
            Dictionary with gap statistics
        """
        if not gaps:
            return {
                'total_gaps': 0,
                'filled_completely': 0,
                'filled_partially': 0,
                'unfilled': 0,
                'avg_fill_time_minutes': 0,
                'avg_gap_size': 0
            }
        
        filled_completely = sum(1 for g in gaps if g.filled_percentage >= 95)
        filled_partially = sum(1 for g in gaps if 5 < g.filled_percentage < 95)
        unfilled = sum(1 for g in gaps if g.filled_percentage <= 5)
        
        # Calculate average fill time for filled gaps
        filled_gaps = [g for g in gaps if g.filled_percentage >= 95]
        avg_fill_time = sum(g.age_minutes for g in filled_gaps) / len(filled_gaps) if filled_gaps else 0
        
        avg_gap_size = sum(g.gap_size for g in gaps) / len(gaps)
        
        return {
            'total_gaps': len(gaps),
            'filled_completely': filled_completely,
            'filled_partially': filled_partially,
            'unfilled': unfilled,
            'avg_fill_time_minutes': int(avg_fill_time),
            'avg_gap_size': round(avg_gap_size, 2)
        }
    
    def find_nearest_gaps(self, 
                         gaps: List[FairValueGap], 
                         current_price: float, 
                         max_gaps: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find nearest gaps above and below current price
        
        Args:
            gaps: List of all detected gaps
            current_price: Current market price
            max_gaps: Maximum number of gaps to return in each direction
            
        Returns:
            Dictionary with 'above' and 'below' lists
        """
        gaps_above = []
        gaps_below = []
        
        for gap in gaps:
            distance = abs(gap.gap_midpoint - current_price)
            gap_info = {
                'level': round(gap.gap_midpoint, 2),
                'timeframe': gap.timeframe,
                'gap_id': gap.gap_id,
                'distance': round(distance, 2),
                'gap_type': gap.gap_type,
                'filled_percentage': round(gap.filled_percentage, 1)
            }
            
            if gap.gap_low > current_price:
                gaps_above.append(gap_info)
            elif gap.gap_high < current_price:
                gaps_below.append(gap_info)
        
        # Sort by distance and limit
        gaps_above.sort(key=lambda x: x['distance'])
        gaps_below.sort(key=lambda x: x['distance'])
        
        return {
            'above_current_price': gaps_above[:max_gaps],
            'below_current_price': gaps_below[:max_gaps]
        }
