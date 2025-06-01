from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, time
import pandas as pd
import numpy as np
import pytz

from src.services.config import TWELVE_DATA_BASE_URL, TWELVE_DATA_API_KEY
from src.services.data import twelvedata_fetcher


async def financial_orb_analysis(
    symbol: str,
    orb_periods: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Calculates Opening Range Breakout (ORB) levels for specified periods.
    
    Args:
        symbol: Stock/ETF symbol (e.g., "SPY", "QQQ")
        orb_periods: List of ORB periods in minutes (default: [5, 15, 30])
    
    Returns:
        Dictionary containing ORB levels, volume analysis, and current position
    """
    
    if orb_periods is None:
        orb_periods = [5, 15, 30]  # Default ORB periods
    
    # Get current time in ET timezone
    et_tz = pytz.timezone('America/New_York')
    current_time_et = datetime.now(et_tz)
    
    # Define market hours (ET)
    market_open = time(9, 30)  # 9:30 AM ET
    market_close = time(16, 0)  # 4:00 PM ET
    
    # For weekends, use last trading day
    if current_time_et.weekday() == 5:  # Saturday
        target_date = current_time_et - timedelta(days=1)
    elif current_time_et.weekday() == 6:  # Sunday
        target_date = current_time_et - timedelta(days=2)
    else:
        target_date = current_time_et
    
    try:
        # Fetch 1-minute data for the trading day
        # We need enough data to cover pre-market and regular hours
        df = twelvedata_fetcher.fetch_time_series(
            symbol=symbol,
            interval="1min",
            outputsize=500  # Covers full trading day
        )
        
        if df is None or df.empty:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Failed to fetch price data"
            }
        
        # Set datetime as index
        if 'datetime' in df.columns:
            df.set_index('datetime', inplace=True)
        
        # Filter for today's regular trading hours only (in ET timezone)
        today_str = target_date.strftime('%Y-%m-%d')
        market_open_time = pd.Timestamp(f"{today_str} 09:30:00", tz=et_tz)
        market_close_time = pd.Timestamp(f"{today_str} 16:00:00", tz=et_tz)
        
        # Ensure the dataframe index is timezone-aware
        if df.index.tz is None:
            df.index = df.index.tz_localize('America/New_York')
        else:
            df.index = df.index.tz_convert('America/New_York')
        
        # Filter dataframe for regular trading hours
        df_rth = df[(df.index >= market_open_time) & (df.index <= market_close_time)].copy()
        
        if df_rth.empty:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "No regular trading hours data available"
            }
        
        # Get current price (most recent)
        current_price = df.iloc[0]['close']
        
        # Calculate average volume for comparison
        avg_volume_per_min = df_rth['volume'].mean()
        
        # Store ORB data for each period
        orb_analysis = {}
        
        for period in orb_periods:
            # Get data for the opening range period
            orb_end_time = market_open_time + timedelta(minutes=period)
            orb_data = df_rth[df_rth.index <= orb_end_time].copy()
            
            if len(orb_data) < period:
                # Not enough data for this ORB period
                orb_analysis[f"{period}min"] = {
                    "status": "insufficient_data",
                    "message": f"Need {period} minutes of data, only have {len(orb_data)}"
                }
                continue
            
            # Calculate ORB levels
            orb_high = orb_data['high'].max()
            orb_low = orb_data['low'].min()
            orb_range = orb_high - orb_low
            orb_midpoint = (orb_high + orb_low) / 2
            
            # Volume analysis during ORB
            orb_volume = orb_data['volume'].sum()
            orb_avg_volume = orb_data['volume'].mean()
            volume_ratio = orb_avg_volume / avg_volume_per_min if avg_volume_per_min > 0 else 0
            
            # Determine current position relative to ORB
            if current_price > orb_high:
                position = "above_range"
                distance_from_range = ((current_price - orb_high) / orb_high) * 100
            elif current_price < orb_low:
                position = "below_range"
                distance_from_range = ((orb_low - current_price) / orb_low) * 100
            else:
                position = "inside_range"
                distance_from_range = 0
            
            # Check for breakout confirmation
            # A breakout is confirmed if price moved beyond ORB and stayed there
            breakout_confirmed = False
            breakout_type = None
            
            # Check data after ORB period  
            post_orb_data = df_rth[df_rth.index > orb_end_time]
            
            if not post_orb_data.empty:
                # Check for bullish breakout
                if any(post_orb_data['close'] > orb_high * 1.001):  # 0.1% buffer
                    # Check if breakout held (at least 3 bars above)
                    bars_above = (post_orb_data['close'] > orb_high).sum()
                    if bars_above >= 3 and position == "above_range":
                        breakout_confirmed = True
                        breakout_type = "bullish"
                
                # Check for bearish breakout
                elif any(post_orb_data['close'] < orb_low * 0.999):  # 0.1% buffer
                    bars_below = (post_orb_data['close'] < orb_low).sum()
                    if bars_below >= 3 and position == "below_range":
                        breakout_confirmed = True
                        breakout_type = "bearish"
            
            # Calculate extension targets
            targets = {
                "bull_0.5x": orb_high + (orb_range * 0.5),
                "bull_1x": orb_high + orb_range,
                "bull_1.5x": orb_high + (orb_range * 1.5),
                "bull_2x": orb_high + (orb_range * 2),
                "bear_0.5x": orb_low - (orb_range * 0.5),
                "bear_1x": orb_low - orb_range,
                "bear_1.5x": orb_low - (orb_range * 1.5),
                "bear_2x": orb_low - (orb_range * 2)
            }
            
            # Identify which targets have been hit
            targets_hit = []
            for target_name, target_level in targets.items():
                if "bull" in target_name and current_price >= target_level:
                    targets_hit.append(target_name)
                elif "bear" in target_name and current_price <= target_level:
                    targets_hit.append(target_name)
            
            # Store analysis for this period
            orb_analysis[f"{period}min"] = {
                "orb_high": round(orb_high, 2),
                "orb_low": round(orb_low, 2),
                "orb_range": round(orb_range, 2),
                "orb_midpoint": round(orb_midpoint, 2),
                "current_price": round(current_price, 2),
                "position": position,
                "distance_from_range_pct": round(distance_from_range, 2),
                "breakout_confirmed": breakout_confirmed,
                "breakout_type": breakout_type,
                "volume_analysis": {
                    "orb_total_volume": int(orb_volume),
                    "orb_avg_volume_per_min": int(orb_avg_volume),
                    "volume_ratio_vs_day_avg": round(volume_ratio, 2),
                    "high_volume": volume_ratio > 1.2
                },
                "targets": {k: round(v, 2) for k, v in targets.items()},
                "targets_hit": targets_hit,
                "orb_start_time": market_open_time.strftime("%Y-%m-%d %H:%M:%S"),
                "orb_end_time": orb_end_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Overall trading bias based on ORB analysis
        trading_bias = analyze_orb_bias(orb_analysis)
        
        # Check for ORB squeeze (narrowing ranges)
        orb_squeeze = detect_orb_squeeze(orb_analysis)
        
        return {
            "symbol": symbol,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "market_session": "regular_hours" if market_open <= current_time_et.time() <= market_close else "closed",
            "orb_analysis": orb_analysis,
            "trading_bias": trading_bias,
            "orb_squeeze": orb_squeeze,
            "current_price": round(current_price, 2)
        }
        
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "message": f"Failed to calculate ORB: {str(e)}"
        }


def analyze_orb_bias(orb_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze overall trading bias based on ORB patterns"""
    
    bullish_signals = 0
    bearish_signals = 0
    strength_factors = []
    
    # Check each ORB period
    for period, data in orb_data.items():
        if isinstance(data, dict) and data.get('status') != 'insufficient_data':
            # Breakout confirmation
            if data.get('breakout_confirmed'):
                if data.get('breakout_type') == 'bullish':
                    bullish_signals += 2
                    strength_factors.append(f"{period} bullish breakout confirmed")
                elif data.get('breakout_type') == 'bearish':
                    bearish_signals += 2
                    strength_factors.append(f"{period} bearish breakout confirmed")
            
            # Position relative to range
            if data.get('position') == 'above_range':
                bullish_signals += 1

            elif data.get('position') == 'below_range':
                bearish_signals += 1
            
            # Volume analysis
            if data.get('volume_analysis', {}).get('high_volume'):
                if data.get('position') == 'above_range':
                    bullish_signals += 1
                    strength_factors.append(f"{period} high volume above range")
                elif data.get('position') == 'below_range':
                    bearish_signals += 1
                    strength_factors.append(f"{period} high volume below range")
            
            # Targets hit
            targets_hit = data.get('targets_hit', [])
            bull_targets = [t for t in targets_hit if 'bull' in t]
            bear_targets = [t for t in targets_hit if 'bear' in t]
            
            if bull_targets:
                bullish_signals += len(bull_targets)
                strength_factors.append(f"{period} hit {len(bull_targets)} bull targets")
            if bear_targets:
                bearish_signals += len(bear_targets)
                strength_factors.append(f"{period} hit {len(bear_targets)} bear targets")
    
    # Determine bias
    if bullish_signals > bearish_signals * 1.5:
        bias = "bullish"
        confidence = "high" if bullish_signals > bearish_signals * 2 else "medium"
    elif bearish_signals > bullish_signals * 1.5:
        bias = "bearish"
        confidence = "high" if bearish_signals > bullish_signals * 2 else "medium"
    else:
        bias = "neutral"
        confidence = "low"
    
    return {
        "bias": bias,
        "confidence": confidence,
        "bullish_signals": bullish_signals,
        "bearish_signals": bearish_signals,
        "strength_factors": strength_factors
    }


def detect_orb_squeeze(orb_data: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if ORB ranges are contracting (potential breakout setup)"""
    
    ranges = []
    periods = []
    
    # Collect valid ORB ranges
    for period, data in orb_data.items():
        if isinstance(data, dict) and data.get('status') != 'insufficient_data':
            if 'orb_range' in data:
                # Extract period number from string (e.g., "5min" -> 5)
                period_num = int(period.replace('min', ''))
                periods.append(period_num)
                ranges.append(data['orb_range'])
    
    if len(ranges) < 2:
        return {
            "squeeze_detected": False,
            "message": "Insufficient ORB periods for squeeze detection"
        }
    
    # Sort by period to ensure proper order
    sorted_data = sorted(zip(periods, ranges))
    periods, ranges = zip(*sorted_data)
    
    # Check if ranges are contracting
    contracting = all(ranges[i] <= ranges[i-1] for i in range(1, len(ranges)))
    
    # Calculate range compression
    if ranges[0] > 0:
        compression_ratio = ranges[-1] / ranges[0]
    else:
        compression_ratio = 1
    
    # Squeeze is detected if ranges are contracting and compression is significant
    squeeze_detected = contracting and compression_ratio < 0.7
    
    return {
        "squeeze_detected": squeeze_detected,
        "contracting_ranges": contracting,
        "compression_ratio": round(compression_ratio, 2),
        "range_progression": {f"{p}min": round(r, 2) for p, r in zip(periods, ranges)},
        "interpretation": "Potential explosive move ahead" if squeeze_detected else "Normal range expansion"
    }
