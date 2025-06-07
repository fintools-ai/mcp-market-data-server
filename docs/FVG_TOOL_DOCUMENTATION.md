# Fair Value Gap (FVG) Analysis Tool Documentation

## Overview

The Fair Value Gap (FVG) tool identifies price imbalances in the market by detecting 3-candle patterns where there's no overlap between the first and third candle. These gaps often act as magnets for price and serve as high-probability support/resistance zones.

## What is a Fair Value Gap?

A Fair Value Gap occurs when:
- **Bullish FVG**: Candle 1 high < Candle 3 low (gap up)
- **Bearish FVG**: Candle 1 low > Candle 3 high (gap down)

The gap represents an area where price moved too quickly, leaving "unfilled" orders behind.

## Tool Usage

```python
# Basic usage
result = await financial_fvg_analysis("AAPL")

# Custom timeframes
result = await financial_fvg_analysis("SPY", timeframes=['1m', '5m', '15m', '30m'])

# Extended lookback
result = await financial_fvg_analysis("TSLA", lookback_periods=1000)
```

## Response Structure

### Main Response
```json
{
  "symbol": "AAPL",
  "status": "success",
  "timestamp": "2024-12-01T14:30:00Z",
  "current_price": 195.50,
  "current_bid": 195.49,
  "current_ask": 195.51,
  "timeframe_data": {...},
  "market_context": {...},
  "gap_statistics": {...},
  "nearest_gaps": {...}
}
```

### Gap Data Structure
Each gap contains:
- `gap_id`: Unique identifier
- `type`: "bullish" or "bearish"
- `price_levels`: Gap boundaries, midpoint, size
- `candle_data`: OHLC for the 3 candles forming the gap
- `volume_data`: Volume analysis during gap formation
- `price_interaction`: How price has tested the gap
- `age_minutes`: How old the gap is
- `filled_percentage`: How much of the gap has been filled

## Key Features

### 1. Multi-Timeframe Analysis
- Analyzes gaps across multiple timeframes simultaneously
- Default: 1m, 5m, 15m
- Customizable via `timeframes` parameter

### 2. Volume Analysis
- Compares volume during gap creation to average
- High volume gaps (>1.5x average) indicate institutional activity
- Volume surge validates gap significance

### 3. Gap Interaction Tracking
- Counts how many times price has tested the gap
- Records lowest/highest tests within gap
- Calculates fill percentage
- Identifies if price is currently inside gap

### 4. Statistical Context
- Historical fill rates by timeframe
- Average time to fill
- Helps assess probability of gap fill

### 5. Nearest Gap Identification
- Lists closest unfilled gaps above/below current price
- Sorted by distance for quick reference
- Includes gap strength indicators

## Trading Applications

### Entry Signals
1. **Retracement to FVG**: Enter when price returns to unfilled gap
2. **Breakout from FVG**: Enter on confirmed break with volume
3. **Gap Fill Completion**: Enter on reversal after gap fills

### Exit Targets
1. **Opposite FVG**: Next gap in direction of trade
2. **Gap Midpoint**: 50% level often acts as target
3. **Complete Fill**: Full gap fill for mean reversion trades

### Risk Management
1. **Stop Loss**: Place beyond gap boundaries
2. **Position Sizing**: Larger gaps = larger stops = smaller position
3. **Time-based**: Consider gap age (older = stronger)

## Integration with Other Tools

### Combine with Volume Profile
```python
# Check if FVG aligns with volume nodes
fvg_result = await financial_fvg_analysis("SPY")
vp_result = await financial_volume_profile("SPY")
# Compare gap levels with POC/VAH/VAL
```

### Combine with Technical Zones
```python
# Validate FVG with other S/R levels
fvg_result = await financial_fvg_analysis("AAPL")
zones_result = await financial_technical_zones("AAPL")
# Look for confluence
```

### Combine with ORB
```python
# Time entries using ORB breakouts toward FVGs
orb_result = await financial_orb_analysis("QQQ")
fvg_result = await financial_fvg_analysis("QQQ")
# Enter on ORB break targeting FVG
```

## Best Practices

### 1. Gap Quality Assessment
- **Size**: Gaps > 0.3% of price are more significant
- **Volume**: High volume gaps are more reliable
- **Age**: Fresh gaps (<2 hours) fill quickly; old gaps are stronger
- **Tests**: Untested gaps are strongest magnets

### 2. Timeframe Selection
- **Scalping**: Use 1m FVGs
- **Day Trading**: Focus on 5m and 15m FVGs
- **Swing Trading**: Use 1h and daily FVGs

### 3. Market Conditions
- **Trending Markets**: Gaps in trend direction are support
- **Range Markets**: All gaps likely to fill
- **High Volatility**: More gaps created, less reliable

### 4. Risk/Reward
- Best setups offer 1:3 or better R:R
- Enter near gap edge, target opposite edge
- Use partial fills for conservative targets

## Common Patterns

### 1. Gap and Go
- Price breaks from gap without filling
- Strong trend continuation signal
- Enter on retest of gap edge

### 2. Gap Fill and Reverse
- Price fills gap then reverses
- Mean reversion opportunity
- Enter at completion of fill

### 3. Partial Fill Hold
- Price fills 50% then bounces
- Midpoint acts as support/resistance
- Enter at midpoint with tight stop

### 4. Multiple Gap Confluence
- Several gaps at similar levels
- Creates strong S/R zone
- Higher probability trades

## Error Handling

The tool returns error status when:
- Symbol not found
- No data available
- API rate limits exceeded
- Network issues

Always check `status` field before using data.

## Performance Considerations

- Default lookback: 500 periods (optimal for intraday)
- Increase for historical analysis
- Decrease for faster response
- Cache results when analyzing multiple symbols

## Limitations

1. Requires liquid instruments (gaps in illiquid stocks less reliable)
2. News-driven gaps may behave differently
3. Weekend gaps excluded from analysis
4. Pre/post-market gaps tracked separately

## Example Trading Workflow

```python
# 1. Identify FVGs
result = await financial_fvg_analysis("SPY")

# 2. Find nearest unfilled gap below price
support_gap = result['nearest_gaps']['below_current_price'][0]

# 3. Set alerts
alert_level = support_gap['level']  # e.g., 445.50

# 4. When price reaches gap
if current_price <= alert_level + 0.10:
    # Enter long position
    entry = alert_level + 0.05
    stop = alert_level - 0.20
    target = current_price + (entry - stop) * 3  # 3:1 R:R

# 5. Manage position
# - Trail stop after 1:1
# - Take partial at 2:1
# - Let rest run to target
```
