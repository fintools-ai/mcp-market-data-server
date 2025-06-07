from typing import Dict, Any, List, Optional
from datetime import datetime, time
import pandas as pd
import pytz

from src.services.config import TWELVE_DATA_BASE_URL, TWELVE_DATA_API_KEY
from src.services.data import twelvedata_fetcher
from src.services.compute.fvg_calculator import FVGCalculator, FairValueGap


async def financial_fvg_analysis(
    symbol: str,
    timeframes: Optional[List[str]] = None,
    lookback_periods: int = 500
) -> Dict[str, Any]:
    """
    Analyzes Fair Value Gaps (FVGs) across multiple timeframes
    
    Args:
        symbol: Stock/ETF symbol (e.g., "SPY", "AAPL")
        timeframes: List of timeframes to analyze (default: ['1m', '5m', '15m'])
        lookback_periods: Number of periods to analyze for gaps
    
    Returns:
        Dictionary containing comprehensive FVG analysis
    """
    
    if timeframes is None:
        timeframes = ['1m', '5m', '15m']
    
    # Initialize calculator
    calculator = FVGCalculator(min_gap_percentage=0.1)
    
    # Get current time in ET timezone
    et_tz = pytz.timezone('America/New_York')
    current_time_et = datetime.now(et_tz)
    
    # Define market hours
    market_open = time(9, 30)
    market_close = time(16, 0)
    
    try:
        # First, get current price from 1-minute data
        df_1m = twelvedata_fetcher.fetch_time_series(
            symbol=symbol,
            interval="1min",
            outputsize=lookback_periods
        )
        
        if df_1m is None or df_1m.empty:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Failed to fetch price data"
            }
        
        # Get current price and market data (most recent is last row since data is chronological)
        current_price = float(df_1m.iloc[-1]['close'])
        current_bid = float(df_1m.iloc[-1]['close'] - 0.01)  # Approximate bid
        current_ask = float(df_1m.iloc[-1]['close'] + 0.01)  # Approximate ask
        
        # Analyze each timeframe
        timeframe_data = {}
        all_gaps = []
        
        for tf in timeframes:
            # Fetch data for timeframe
            if tf == '1m':
                df = df_1m  # Reuse already fetched data
            else:
                df = twelvedata_fetcher.fetch_time_series(
                    symbol=symbol,
                    interval=tf,
                    outputsize=lookback_periods
                )
            
            if df is None or df.empty:
                timeframe_data[tf] = {
                    "fvg_count": 0,
                    "gaps": [],
                    "error": "Failed to fetch data"
                }
                continue
            
            # Detect FVGs
            gaps = calculator.detect_fvgs(
                df=df,
                timeframe=tf,
                current_price=current_price,
                lookback_periods=lookback_periods
            )
            
            # Convert gaps to dict format
            gaps_dict = []
            for gap in gaps:
                gap_dict = {
                    "gap_id": gap.gap_id,
                    "type": gap.gap_type,
                    "candle_times": {
                        "candle_1": gap.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if isinstance(gap.timestamp, datetime) else str(gap.timestamp),
                        "candle_2": "N/A",  # Could calculate if needed
                        "candle_3": "N/A"   # Could calculate if needed
                    },
                    "price_levels": {
                        "gap_high": round(gap.gap_high, 2),
                        "gap_low": round(gap.gap_low, 2),
                        "gap_midpoint": round(gap.gap_midpoint, 2),
                        "gap_size": round(gap.gap_size, 2)
                    },
                    "candle_data": gap.candle_data,
                    "volume_data": gap.volume_data,
                    "price_interaction": {
                        "times_tested": gap.times_tested,
                        "lowest_test": round(gap.lowest_test, 2) if gap.lowest_test else None,
                        "highest_test": round(gap.highest_test, 2) if gap.highest_test else None,
                        "currently_inside_gap": gap.currently_inside_gap
                    },
                    "age_minutes": gap.age_minutes,
                    "filled_percentage": round(gap.filled_percentage, 1)
                }
                gaps_dict.append(gap_dict)
            
            timeframe_data[tf] = {
                "fvg_count": len(gaps),
                "gaps": gaps_dict
            }
            
            all_gaps.extend(gaps)
        
        # Calculate market context
        intraday_high = float(df_1m['high'].max())
        intraday_low = float(df_1m['low'].min())
        opening_price = float(df_1m.iloc[0]['open']) if len(df_1m) > 0 else current_price
        
        # Volume calculations
        volume_today = int(df_1m['volume'].sum())
        avg_volume_per_min = int(df_1m['volume'].mean())
        estimated_daily_volume = avg_volume_per_min * 390  # 390 minutes in trading day
        
        market_context = {
            "session": "regular_trading" if market_open <= current_time_et.time() <= market_close else "pre_market",
            "minutes_since_open": int((current_time_et.hour * 60 + current_time_et.minute) - (9 * 60 + 30)),
            "minutes_until_close": int((16 * 60) - (current_time_et.hour * 60 + current_time_et.minute)),
            "intraday_high": round(intraday_high, 2),
            "intraday_low": round(intraday_low, 2),
            "opening_price": round(opening_price, 2),
            "volume_today": volume_today,
            "avg_daily_volume": estimated_daily_volume
        }
        
        # Calculate gap statistics for each timeframe
        gap_statistics = {}
        for tf in timeframes:
            tf_gaps = [g for g in all_gaps if g.timeframe == tf]
            gap_statistics[tf] = calculator.calculate_gap_statistics(tf_gaps, tf)
        
        # Find nearest gaps
        nearest_gaps = calculator.find_nearest_gaps(all_gaps, current_price)
        
        return {
            "symbol": symbol,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "current_price": round(current_price, 2),
            "current_bid": round(current_bid, 2),
            "current_ask": round(current_ask, 2),
            "timeframe_data": timeframe_data,
            "market_context": market_context,
            "gap_statistics": gap_statistics,
            "nearest_gaps": nearest_gaps
        }
        
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "message": f"Failed to analyze FVGs: {str(e)}"
        }
