# ORB (Opening Range Breakout) Tool Documentation

## Overview

The ORB tool analyzes Opening Range Breakout patterns, a critical indicator for intraday and 0DTE options trading. It identifies key price levels established during the market's opening period and tracks breakouts for trading opportunities.

## Features

### 1. **Multi-Period Analysis**
- Analyzes 5-minute, 15-minute, and 30-minute opening ranges simultaneously
- Each period suitable for different trading styles:
  - **5-min**: Aggressive scalping and quick 0DTE entries
  - **15-min**: Standard intraday setups
  - **30-min**: Conservative swing entries

### 2. **Comprehensive Metrics**
For each ORB period, the tool provides:

- **Price Levels**:
  - ORB High and Low
  - Range size
  - Midpoint
  - Current price position (above/below/inside range)

- **Breakout Analysis**:
  - Breakout confirmation (requires 3+ bars beyond range)
  - Breakout type (bullish/bearish)
  - Distance from range as percentage

- **Volume Analysis**:
  - Total volume during ORB period
  - Average volume per minute
  - Volume ratio vs day average
  - High volume detection (>1.2x average)

- **Extension Targets**:
  - Bull targets: 0.5x, 1x, 1.5x, 2x range extensions above ORB high
  - Bear targets: 0.5x, 1x, 1.5x, 2x range extensions below ORB low
  - Tracks which targets have been hit

### 3. **Trading Intelligence**

- **Overall Trading Bias**:
  - Analyzes signals across all periods
  - Provides bias direction (bullish/bearish/neutral)
  - Confidence level (high/medium/low)
  - Lists strength factors

- **ORB Squeeze Detection**:
  - Identifies contracting ranges (5min > 15min > 30min)
  - Calculates compression ratio
  - Alerts to potential explosive moves

## Usage Examples

### Basic Call
```python
result = await analyze_open_interest("SPY")
```

### Response Structure
```json
{
  "symbol": "SPY",
  "status": "success",
  "timestamp": "2024-03-15T14:30:00Z",
  "market_session": "regular_hours",
  "current_price": 425.50,
  "orb_analysis": {
    "5min": {
      "orb_high": 424.75,
      "orb_low": 424.25,
      "orb_range": 0.50,
      "orb_midpoint": 424.50,
      "current_price": 425.50,
      "position": "above_range",
      "distance_from_range_pct": 0.18,
      "breakout_confirmed": true,
      "breakout_type": "bullish",
      "volume_analysis": {
        "orb_total_volume": 2500000,
        "orb_avg_volume_per_min": 500000,
        "volume_ratio_vs_day_avg": 1.35,
        "high_volume": true
      },
      "targets": {
        "bull_0.5x": 425.00,
        "bull_1x": 425.25,
        "bull_1.5x": 425.50,
        "bull_2x": 425.75,
        "bear_0.5x": 424.00,
        "bear_1x": 423.75,
        "bear_1.5x": 423.50,
        "bear_2x": 423.25
      },
      "targets_hit": ["bull_0.5x", "bull_1x", "bull_1.5x"],
      "orb_start_time": "2024-03-15 09:30:00",
      "orb_end_time": "2024-03-15 09:35:00"
    },
    "15min": { ... },
    "30min": { ... }
  },
  "trading_bias": {
    "bias": "bullish",
    "confidence": "high",
    "bullish_signals": 8,
    "bearish_signals": 1,
    "strength_factors": [
      "5min bullish breakout confirmed",
      "5min high volume above range",
      "15min hit 2 bull targets"
    ]
  },
  "orb_squeeze": {
    "squeeze_detected": false,
    "contracting_ranges": false,
    "compression_ratio": 0.95,
    "range_progression": {
      "5min": 0.50,
      "15min": 0.65,
      "30min": 0.48
    },
    "interpretation": "Normal range expansion"
  }
}
```

## Trading Strategies

### 1. **Classic ORB Breakout**
- Wait for price to break above/below 15-min ORB
- Confirm with volume (>1.2x average)
- Enter on retest of ORB level
- Target: 1x extension, Stop: ORB midpoint

### 2. **ORB Squeeze Play**
- Identify when squeeze_detected = true
- Wait for breakout from tightest range (usually 30-min)
- High probability of explosive move
- Target: 2x extension minimum

### 3. **Multi-Timeframe Confirmation**
- All periods show same bias
- High confidence rating
- Enter on shortest timeframe breakout
- Hold for longer timeframe targets

### 4. **Failed ORB Reversal**
- Price breaks ORB but breakout_confirmed = false
- Re-enters range and breaks opposite side
- High probability reversal setup
- Target: Opposite ORB extreme

## Integration with Other Tools

### Combined with Volume Profile:
```python
orb_result = await analyze_open_interest("SPY")
vp_result = await financial_volume_profile_tool("SPY")

# Check if ORB high aligns with VAH (Value Area High)
if abs(orb_result['orb_analysis']['15min']['orb_high'] - 
       vp_result['timeframe_volume_profile']['5m']['volume_profile_structure']['value_area_high']) < 0.50:
    print("Strong resistance confluence at ORB high!")
```

### Combined with Technical Analysis:
```python
orb_result = await analyze_open_interest("QQQ")
ta_result = await financial_technical_analysis_tool("QQQ")

# Check if bullish ORB breakout has momentum confirmation
if (orb_result['trading_bias']['bias'] == 'bullish' and 
    ta_result['timeframe_technical_analysis']['5m']['technical_analysis']['oscillators']['rsi_14'] > 50):
    print("Bullish ORB with positive momentum!")
```

## Best Practices

1. **Time Considerations**:
   - ORB is most reliable in first 2 hours of trading
   - Avoid using near market close
   - Best for liquid symbols (SPY, QQQ, major stocks)

2. **Risk Management**:
   - Never risk more than ORB range on a trade
   - Use ORB midpoint as initial stop
   - Scale out at extension targets

3. **Market Context**:
   - Check pre-market levels
   - Be aware of economic events at 10 AM
   - Consider overall market trend

4. **0DTE Specific**:
   - Use 5-min ORB for quick entries
   - Focus on high volume breakouts
   - Take profits quickly at first target

## Limitations

- Requires at least 30 minutes of RTH data
- Less reliable on low-volume symbols
- May give false signals in choppy markets
- Weekend/holiday data uses last trading day

## Error Handling

The tool handles various edge cases:
- Insufficient data: Returns status per timeframe
- Weekend queries: Automatically uses last trading day
- Pre-market queries: Waits for regular hours data
- API failures: Returns error status with message
