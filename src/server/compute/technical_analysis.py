import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta


def calculate_volume_profile(df: pd.DataFrame, num_bins: int = 20, price_precision: int = 2) -> Optional[Dict[str, Any]]:
    """
    Calculate Volume Profile from OHLCV data.
    
    Args:
        df: DataFrame with OHLC and volume data
        num_bins: Number of price bins for volume distribution
        price_precision: Decimal places for price rounding
        
    Returns:
        Dictionary containing POC, VAH, VAL, and volume nodes
    """
    if df is None or df.empty:
        return None
        
    if not all(col in df.columns for col in ['high', 'low', 'volume']):
        print("Error: DataFrame missing required columns for Volume Profile calculation")
        return None
        
    try:
        # Calculate price range
        price_min = df['low'].min()
        price_max = df['high'].max()
        
        if price_min >= price_max:
            print("Error: Invalid price range for Volume Profile calculation")
            return None
            
        # Create price bins
        bins = np.linspace(price_min, price_max, num_bins + 1)
        bin_width = bins[1] - bins[0]
        
        # Calculate volume at each price level
        volume_by_price = {}
        
        for idx, row in df.iterrows():
            # Distribute volume across the bar's range
            bar_low = row['low']
            bar_high = row['high']
            bar_volume = row['volume']
            
            # Find which bins this bar spans
            low_bin_idx = np.searchsorted(bins, bar_low, side='left')
            high_bin_idx = np.searchsorted(bins, bar_high, side='right')
            
            # Distribute volume evenly across spanned bins
            if high_bin_idx > low_bin_idx:
                volume_per_bin = bar_volume / (high_bin_idx - low_bin_idx)
                
                for bin_idx in range(low_bin_idx, high_bin_idx):
                    if 0 <= bin_idx < len(bins) - 1:
                        bin_price = round((bins[bin_idx] + bins[bin_idx + 1]) / 2, price_precision)
                        volume_by_price[bin_price] = volume_by_price.get(bin_price, 0) + volume_per_bin
        
        if not volume_by_price:
            print("Error: No volume data calculated for Volume Profile")
            return None
            
        # Sort by volume to find key levels
        sorted_prices = sorted(volume_by_price.items(), key=lambda x: x[1], reverse=True)
        
        # Point of Control (POC) - highest volume price
        poc = sorted_prices[0][0]
        
        # Calculate Value Area (70% of volume)
        total_volume = sum(v for _, v in sorted_prices)
        value_area_volume = total_volume * 0.7
        
        # Build value area around POC
        value_area_prices = [poc]
        accumulated_volume = volume_by_price[poc]
        
        # Expand from POC outward
        poc_idx = next(i for i, (p, _) in enumerate(sorted_prices) if p == poc)
        
        # Get all prices sorted by price (not volume) for expansion
        all_prices_sorted = sorted(volume_by_price.keys())
        poc_price_idx = all_prices_sorted.index(poc)
        
        left_idx = poc_price_idx - 1
        right_idx = poc_price_idx + 1
        
        while accumulated_volume < value_area_volume:
            left_volume = volume_by_price.get(all_prices_sorted[left_idx], 0) if left_idx >= 0 else 0
            right_volume = volume_by_price.get(all_prices_sorted[right_idx], 0) if right_idx < len(all_prices_sorted) else 0
            
            if left_volume >= right_volume and left_idx >= 0:
                value_area_prices.append(all_prices_sorted[left_idx])
                accumulated_volume += left_volume
                left_idx -= 1
            elif right_idx < len(all_prices_sorted):
                value_area_prices.append(all_prices_sorted[right_idx])
                accumulated_volume += right_volume
                right_idx += 1
            else:
                break
                
        vah = max(value_area_prices)
        val = min(value_area_prices)
        
        # Identify High Volume Nodes (HVN) and Low Volume Nodes (LVN)
        # HVN: Top 20% by volume
        hvn_threshold = sorted_prices[int(len(sorted_prices) * 0.2)][1] if len(sorted_prices) > 5 else sorted_prices[-1][1]
        hvns = []
        
        # Group nearby high volume prices
        for price, volume in sorted_prices:
            if volume >= hvn_threshold:
                # Check if close to existing HVN
                merged = False
                for hvn in hvns:
                    if abs(price - hvn['start']) <= bin_width * 1.5:
                        hvn['end'] = max(hvn['end'], price)
                        hvn['start'] = min(hvn['start'], price)
                        hvn['volume'] = max(hvn['volume'], volume)
                        merged = True
                        break
                        
                if not merged:
                    hvns.append({
                        'start': round(price - bin_width/2, price_precision),
                        'end': round(price + bin_width/2, price_precision),
                        'volume': volume
                    })
        
        # LVN: Bottom 20% by volume
        lvn_threshold = sorted_prices[int(len(sorted_prices) * 0.8)][1] if len(sorted_prices) > 5 else sorted_prices[0][1]
        lvns = []
        
        for price, volume in reversed(sorted_prices):
            if volume <= lvn_threshold:
                # Check if close to existing LVN
                merged = False
                for lvn in lvns:
                    if abs(price - lvn['start']) <= bin_width * 1.5:
                        lvn['end'] = max(lvn['end'], price)
                        lvn['start'] = min(lvn['start'], price)
                        lvn['volume'] = min(lvn['volume'], volume)
                        merged = True
                        break
                        
                if not merged:
                    lvns.append({
                        'start': round(price - bin_width/2, price_precision),
                        'end': round(price + bin_width/2, price_precision),
                        'volume': volume
                    })
        
        return {
            'point_of_control': round(poc, price_precision),
            'value_area_high': round(vah, price_precision),
            'value_area_low': round(val, price_precision),
            'high_volume_nodes': hvns[:5],  # Limit to top 5
            'low_volume_nodes': lvns[:5],   # Limit to top 5
            'total_volume': float(total_volume),
            'value_area_volume': float(accumulated_volume),
            'value_area_percentage': round(accumulated_volume / total_volume * 100, 2)
        }
        
    except Exception as e:
        print(f"Error calculating Volume Profile: {str(e)}")
        return None


def calculate_fibonacci_levels(df: pd.DataFrame, lookback_periods: int = 50, price_precision: int = 2) -> List[Dict[str, Any]]:
    """
    Calculate Fibonacci retracement and extension levels.
    
    Args:
        df: DataFrame with OHLC data
        lookback_periods: Number of periods to look back for swing points
        price_precision: Decimal places for price rounding
        
    Returns:
        List of Fibonacci zones
    """
    if df is None or df.empty or len(df) < lookback_periods:
        return []
        
    try:
        # Get recent high and low
        recent_df = df.tail(lookback_periods)
        swing_high = recent_df['high'].max()
        swing_low = recent_df['low'].min()
        
        if swing_high <= swing_low:
            return []
            
        # Calculate Fibonacci levels
        price_range = swing_high - swing_low
        
        fib_levels = {
            '0.0': swing_low,
            '0.236': swing_low + price_range * 0.236,
            '0.382': swing_low + price_range * 0.382,
            '0.5': swing_low + price_range * 0.5,
            '0.618': swing_low + price_range * 0.618,
            '0.786': swing_low + price_range * 0.786,
            '1.0': swing_high,
            '1.272': swing_high + price_range * 0.272,
            '1.618': swing_high + price_range * 0.618
        }
        
        # Determine current price position
        current_price = df['close'].iloc[-1]
        
        zones = []
        
        # Add retracement levels as support/resistance
        for level_name, level_price in fib_levels.items():
            level_value = float(level_name)
            
            if level_value <= 1.0:
                # Retracement levels
                if current_price > level_price:
                    zone_type = "SUPPORT"
                else:
                    zone_type = "RESISTANCE"
            else:
                # Extension levels
                zone_type = "TARGET_UPSIDE"
                
            zones.append({
                'type': zone_type,
                'name': f'Fib {level_name}',
                'level': round(level_price, price_precision),
                'source': f'Fibonacci ({lookback_periods} bars)'
            })
            
        return zones
        
    except Exception as e:
        print(f"Error calculating Fibonacci levels: {str(e)}")
        return []


def calculate_ichimoku(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculate Ichimoku Cloud indicators.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        Dictionary containing Ichimoku values
    """
    if df is None or df.empty or len(df) < 52:  # Need at least 52 periods for Ichimoku
        return None
        
    try:
        # Ichimoku parameters
        tenkan_period = 9
        kijun_period = 26
        senkou_b_period = 52
        
        # Tenkan-sen (Conversion Line)
        tenkan_high = df['high'].rolling(window=tenkan_period).max()
        tenkan_low = df['low'].rolling(window=tenkan_period).min()
        tenkan_sen = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = df['high'].rolling(window=kijun_period).max()
        kijun_low = df['low'].rolling(window=kijun_period).min()
        kijun_sen = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        
        # Senkou Span B (Leading Span B)
        senkou_b_high = df['high'].rolling(window=senkou_b_period).max()
        senkou_b_low = df['low'].rolling(window=senkou_b_period).min()
        senkou_span_b = ((senkou_b_high + senkou_b_low) / 2).shift(kijun_period)
        
        # Chikou Span (Lagging Span)
        chikou_span = df['close'].shift(-kijun_period)
        
        # Get current values
        current_idx = len(df) - 1
        
        # Determine cloud status
        current_price = df['close'].iloc[-1]
        span_a_current = senkou_span_a.iloc[current_idx] if not pd.isna(senkou_span_a.iloc[current_idx]) else None
        span_b_current = senkou_span_b.iloc[current_idx] if not pd.isna(senkou_span_b.iloc[current_idx]) else None
        
        cloud_status = "neutral"
        if span_a_current and span_b_current:
            if current_price > max(span_a_current, span_b_current):
                cloud_status = "bullish"
            elif current_price < min(span_a_current, span_b_current):
                cloud_status = "bearish"
                
        # Trend strength
        tenkan_current = tenkan_sen.iloc[current_idx] if not pd.isna(tenkan_sen.iloc[current_idx]) else None
        kijun_current = kijun_sen.iloc[current_idx] if not pd.isna(kijun_sen.iloc[current_idx]) else None
        
        trend_strength = "neutral"
        if tenkan_current and kijun_current:
            if tenkan_current > kijun_current:
                trend_strength = "bullish"
            elif tenkan_current < kijun_current:
                trend_strength = "bearish"
                
        return {
            'tenkan_sen': float(tenkan_current) if tenkan_current else None,
            'kijun_sen': float(kijun_current) if kijun_current else None,
            'senkou_span_a': float(span_a_current) if span_a_current else None,
            'senkou_span_b': float(span_b_current) if span_b_current else None,
            'chikou_span': float(chikou_span.iloc[-kijun_period]) if len(df) > kijun_period and not pd.isna(chikou_span.iloc[-kijun_period]) else None,
            'cloud_status': cloud_status,
            'trend_strength': trend_strength
        }
        
    except Exception as e:
        print(f"Error calculating Ichimoku: {str(e)}")
        return None


def identify_large_volume_bars(df: pd.DataFrame, volume_threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
    """
    Identify bars with unusually large volume.
    
    Args:
        df: DataFrame with OHLC and volume data
        volume_threshold_multiplier: Multiplier for average volume to identify large bars
        
    Returns:
        List of large volume bar information
    """
    if df is None or df.empty or 'volume' not in df.columns:
        return []
        
    try:
        # Calculate average volume
        avg_volume = df['volume'].mean()
        threshold = avg_volume * volume_threshold_multiplier
        
        large_volume_bars = []
        
        for idx, row in df.tail(20).iterrows():  # Check last 20 bars
            if row['volume'] > threshold:
                # Determine bar type
                bar_type = "neutral"
                if row['close'] > row['open']:
                    bar_type = "bullish"
                elif row['close'] < row['open']:
                    bar_type = "bearish"
                    
                large_volume_bars.append({
                    'timestamp': row['datetime'].isoformat() if 'datetime' in df.columns and pd.notna(row['datetime']) else None,
                    'volume': float(row['volume']),
                    'volume_ratio': round(row['volume'] / avg_volume, 2),
                    'type': bar_type,
                    'price_change': round((row['close'] - row['open']) / row['open'] * 100, 2)
                })
                
        return large_volume_bars
        
    except Exception as e:
        print(f"Error identifying large volume bars: {str(e)}")
        return []


def calculate_volume_momentum_indicators(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculate volume-based momentum indicators.
    
    Args:
        df: DataFrame with OHLC and volume data
        
    Returns:
        Dictionary containing volume momentum indicators
    """
    if df is None or df.empty or len(df) < 20:
        return None
        
    try:
        # On Balance Volume (OBV)
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
                
        df['obv'] = obv
        
        # Chaikin Money Flow (CMF)
        mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mfm = mfm.fillna(0)  # Handle division by zero
        mf_volume = mfm * df['volume']
        
        cmf_period = 20
        cmf = mf_volume.rolling(window=cmf_period).sum() / df['volume'].rolling(window=cmf_period).sum()
        
        # Volume Rate of Change (VROC)
        vroc_period = 14
        vroc = ((df['volume'] - df['volume'].shift(vroc_period)) / df['volume'].shift(vroc_period)) * 100
        
        # Current values
        current_obv = df['obv'].iloc[-1]
        current_cmf = cmf.iloc[-1] if not pd.isna(cmf.iloc[-1]) else 0
        current_vroc = vroc.iloc[-1] if not pd.isna(vroc.iloc[-1]) else 0
        
        # Buying/Selling pressure
        recent_bars = min(10, len(df))
        up_volume = df[df['close'] > df['open']].tail(recent_bars)['volume'].sum()
        down_volume = df[df['close'] < df['open']].tail(recent_bars)['volume'].sum()
        total_recent_volume = up_volume + down_volume
        
        buying_pressure = {
            'up_volume': float(up_volume),
            'down_volume': float(down_volume),
            'up_ratio': round(up_volume / total_recent_volume, 3) if total_recent_volume > 0 else 0.5,
            'is_bullish_volume': up_volume > down_volume
        }
        
        return {
            'obv': float(current_obv),
            'cmf': round(float(current_cmf), 4),
            'vroc': round(float(current_vroc), 2),
            'buying_pressure': buying_pressure
        }
        
    except Exception as e:
        print(f"Error calculating volume momentum indicators: {str(e)}")
        return None


def calculate_trend_strength(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculate trend strength indicators.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        Dictionary containing trend strength metrics
    """
    if df is None or df.empty or len(df) < 50:
        return None
        
    try:
        # ADX calculation
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        # Directional movement
        up_move = df['high'] - df['high'].shift()
        down_move = df['low'].shift() - df['low']
        
        pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        pos_di = pd.Series(pos_dm).rolling(window=14).sum() / atr * 100
        neg_di = pd.Series(neg_dm).rolling(window=14).sum() / atr * 100
        
        dx = np.abs(pos_di - neg_di) / (pos_di + neg_di) * 100
        adx = pd.Series(dx).rolling(window=14).mean()
        
        # Moving average analysis
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        # Current values
        current_price = df['close'].iloc[-1]
        current_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0
        current_sma20 = df['sma20'].iloc[-1] if not pd.isna(df['sma20'].iloc[-1]) else current_price
        current_sma50 = df['sma50'].iloc[-1] if not pd.isna(df['sma50'].iloc[-1]) else current_price
        current_ema20 = df['ema20'].iloc[-1] if not pd.isna(df['ema20'].iloc[-1]) else current_price
        
        # Calculate slopes
        ema20_slope = (current_ema20 - df['ema20'].iloc[-5]) / 5 if len(df) >= 5 else 0
        
        # Price distance from moving averages
        distance_from_sma20 = ((current_price - current_sma20) / current_sma20) * 100
        distance_from_sma50 = ((current_price - current_sma50) / current_sma50) * 100
        
        # Trend determination
        trend = "neutral"
        if current_price > current_sma20 and current_sma20 > current_sma50:
            trend = "strong_uptrend"
        elif current_price > current_sma20:
            trend = "uptrend"
        elif current_price < current_sma20 and current_sma20 < current_sma50:
            trend = "strong_downtrend"
        elif current_price < current_sma20:
            trend = "downtrend"
            
        return {
            'adx': round(float(current_adx), 2),
            'trend': trend,
            'ema20_slope': round(float(ema20_slope), 4),
            'price_distance_from_sma20': round(float(distance_from_sma20), 2),
            'price_distance_from_sma50': round(float(distance_from_sma50), 2),
            'is_trending': current_adx > 25
        }
        
    except Exception as e:
        print(f"Error calculating trend strength: {str(e)}")
        return None


def detect_divergences(df: pd.DataFrame, lookback: int = 20) -> Optional[Dict[str, Any]]:
    """
    Detect price/momentum divergences.
    
    Args:
        df: DataFrame with OHLC data
        lookback: Number of periods to look back for divergence
        
    Returns:
        Dictionary containing divergence information
    """
    if df is None or df.empty or len(df) < lookback + 14:  # Need extra for RSI calculation
        return None
        
    try:
        # Calculate RSI for divergence detection
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Look for divergences in recent data
        recent_data = df.tail(lookback)
        recent_rsi = rsi.tail(lookback)
        
        # Find local highs and lows
        price_highs = []
        price_lows = []
        rsi_highs = []
        rsi_lows = []
        
        for i in range(1, len(recent_data) - 1):
            # Price highs/lows
            if recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1]:
                price_highs.append((i, recent_data['high'].iloc[i]))
            if recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1]:
                price_lows.append((i, recent_data['low'].iloc[i]))
                
            # RSI highs/lows
            if recent_rsi.iloc[i] > recent_rsi.iloc[i-1] and recent_rsi.iloc[i] > recent_rsi.iloc[i+1]:
                rsi_highs.append((i, recent_rsi.iloc[i]))
            if recent_rsi.iloc[i] < recent_rsi.iloc[i-1] and recent_rsi.iloc[i] < recent_rsi.iloc[i+1]:
                rsi_lows.append((i, recent_rsi.iloc[i]))
        
        # Check for divergences
        bullish_divergence = False
        bearish_divergence = False
        
        # Bullish divergence: lower lows in price, higher lows in RSI
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            if price_lows[-1][1] < price_lows[-2][1] and rsi_lows[-1][1] > rsi_lows[-2][1]:
                bullish_divergence = True
                
        # Bearish divergence: higher highs in price, lower highs in RSI
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            if price_highs[-1][1] > price_highs[-2][1] and rsi_highs[-1][1] < rsi_highs[-2][1]:
                bearish_divergence = True
                
        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence,
            'current_rsi': round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None
        }
        
    except Exception as e:
        print(f"Error detecting divergences: {str(e)}")
        return None
