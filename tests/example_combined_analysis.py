#!/usr/bin/env python3
"""
Example: Complete trading analysis using FVG with other tools
This demonstrates how to combine all tools for comprehensive market analysis
"""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.tools.fvg_tool import financial_fvg_analysis
from src.services.tools.volume_profile_tool import financial_volume_profile
from src.services.tools.technical_zones_tool import financial_technical_zones
from src.services.tools.orb_tool import financial_orb_analysis


async def comprehensive_analysis(symbol: str):
    """Perform comprehensive analysis using all tools"""
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE TRADING ANALYSIS FOR {symbol}")
    print('='*80)
    
    # Run all analyses in parallel for efficiency
    fvg_task = financial_fvg_analysis(symbol)
    vp_task = financial_volume_profile(symbol)
    zones_task = financial_technical_zones(symbol)
    orb_task = financial_orb_analysis(symbol)
    
    # Wait for all results
    fvg_result, vp_result, zones_result, orb_result = await asyncio.gather(
        fvg_task, vp_task, zones_task, orb_task
    )
    
    # Extract key data
    current_price = fvg_result['current_price']
    
    print(f"\n📊 CURRENT PRICE: ${current_price}")
    print("="*80)
    
    # 1. FVG Analysis
    print("\n🔍 FAIR VALUE GAP ANALYSIS:")
    print("-"*40)
    
    # Find nearest unfilled gaps
    gaps_above = fvg_result['nearest_gaps']['above_current_price']
    gaps_below = fvg_result['nearest_gaps']['below_current_price']
    
    if gaps_below:
        nearest_support_gap = gaps_below[0]
        print(f"Nearest Support Gap: ${nearest_support_gap['level']} ({nearest_support_gap['timeframe']}) - {nearest_support_gap['distance']:.2f} below")
    
    if gaps_above:
        nearest_resistance_gap = gaps_above[0]
        print(f"Nearest Resistance Gap: ${nearest_resistance_gap['level']} ({nearest_resistance_gap['timeframe']}) - {nearest_resistance_gap['distance']:.2f} above")
    
    # Count active gaps
    total_active_gaps = sum(data['fvg_count'] for data in fvg_result['timeframe_data'].values())
    print(f"\nTotal Active FVGs: {total_active_gaps}")
    
    # 2. Volume Profile Analysis
    print("\n📊 VOLUME PROFILE ANALYSIS:")
    print("-"*40)
    
    if vp_result['status'] == 'success':
        # Get 5m volume profile
        vp_5m = vp_result['timeframe_volume_profile'].get('5m', {})
        if vp_5m:
            vp_structure = vp_5m.get('volume_profile_structure', {})
            poc = vp_structure.get('point_of_control')
            vah = vp_structure.get('value_area_high')
            val = vp_structure.get('value_area_low')
            
            if poc:
                print(f"Point of Control (POC): ${poc:.2f}")
            if vah and val:
                print(f"Value Area: ${val:.2f} - ${vah:.2f}")
            
            # Check if current price is in value area
            if val and vah and val <= current_price <= vah:
                print("✓ Price is within value area (balanced)")
            elif val and current_price < val:
                print("⚠️ Price below value area (potentially oversold)")
            elif vah and current_price > vah:
                print("⚠️ Price above value area (potentially overbought)")
    
    # 3. Technical Zones
    print("\n🎯 KEY TECHNICAL ZONES:")
    print("-"*40)
    
    if zones_result['status'] == 'success':
        # Get 5m zones
        zones_5m = zones_result['timeframe_zones'].get('5m', {})
        if zones_5m:
            zones = zones_5m.get('zones', [])
            
            # Find nearest support and resistance
            support_zones = [z for z in zones if z['type'] == 'SUPPORT' and z['level'] < current_price]
            resistance_zones = [z for z in zones if z['type'] == 'RESISTANCE' and z['level'] > current_price]
            
            if support_zones:
                nearest_support = max(support_zones, key=lambda x: x['level'])
                print(f"Nearest Support: ${nearest_support['level']:.2f} ({nearest_support['source']}) - Strength: {nearest_support['strength']}")
            
            if resistance_zones:
                nearest_resistance = min(resistance_zones, key=lambda x: x['level'])
                print(f"Nearest Resistance: ${nearest_resistance['level']:.2f} ({nearest_resistance['source']}) - Strength: {nearest_resistance['strength']}")
    
    # 4. ORB Analysis
    print("\n📈 OPENING RANGE BREAKOUT STATUS:")
    print("-"*40)
    
    if orb_result['status'] == 'success':
        orb_5min = orb_result['orb_analysis'].get('5min', {})
        if isinstance(orb_5min, dict) and 'orb_high' in orb_5min:
            print(f"5min ORB Range: ${orb_5min['orb_low']:.2f} - ${orb_5min['orb_high']:.2f}")
            print(f"Current Position: {orb_5min['position']}")
            
            if orb_5min.get('breakout_confirmed'):
                print(f"✓ Breakout Confirmed: {orb_5min['breakout_type'].upper()}")
            
            # Show trading bias
            bias = orb_result.get('trading_bias', {})
            if bias:
                print(f"\nTrading Bias: {bias.get('bias', 'neutral').upper()} (Confidence: {bias.get('confidence', 'low')})")
    
    # 5. CONFLUENCE ANALYSIS
    print("\n🔄 CONFLUENCE ANALYSIS:")
    print("-"*40)
    
    confluences = []
    
    # Check for FVG + Volume Profile confluence
    if gaps_below and poc:
        gap_level = gaps_below[0]['level']
        if abs(gap_level - poc) < 0.50:  # Within $0.50
            confluences.append(f"FVG Support at ${gap_level:.2f} aligns with POC at ${poc:.2f}")
    
    # Check for multiple tool agreement
    if gaps_below and support_zones:
        gap_level = gaps_below[0]['level']
        zone_level = nearest_support['level']
        if abs(gap_level - zone_level) < 0.30:
            confluences.append(f"FVG and Technical Zone confluence at ${gap_level:.2f}-${zone_level:.2f}")
    
    if confluences:
        print("✓ Strong Confluence Found:")
        for c in confluences:
            print(f"  - {c}")
    else:
        print("⚠️ No significant confluence detected")
    
    # 6. TRADING RECOMMENDATIONS
    print("\n💡 TRADING SETUP RECOMMENDATIONS:")
    print("-"*40)
    
    # Generate recommendations based on analysis
    if gaps_below and current_price - gaps_below[0]['level'] < 1.00:
        support_gap = gaps_below[0]
        print(f"\n🟢 LONG SETUP:")
        print(f"  Entry Zone: ${support_gap['level']:.2f} - ${support_gap['level'] + 0.10:.2f}")
        print(f"  Stop Loss: ${support_gap['level'] - 0.20:.2f}")
        
        if gaps_above:
            target = gaps_above[0]['level']
            print(f"  Target 1: ${target:.2f} (next FVG)")
            rr_ratio = (target - support_gap['level']) / 0.20
            print(f"  Risk/Reward: 1:{rr_ratio:.1f}")
    
    if gaps_above and gaps_above[0]['level'] - current_price < 1.00:
        resistance_gap = gaps_above[0]
        print(f"\n🔴 SHORT SETUP:")
        print(f"  Entry Zone: ${resistance_gap['level'] - 0.10:.2f} - ${resistance_gap['level']:.2f}")
        print(f"  Stop Loss: ${resistance_gap['level'] + 0.20:.2f}")
        
        if gaps_below:
            target = gaps_below[0]['level']
            print(f"  Target 1: ${target:.2f} (next FVG)")
            rr_ratio = (resistance_gap['level'] - target) / 0.20
            print(f"  Risk/Reward: 1:{rr_ratio:.1f}")
    
    print("\n" + "="*80)


async def main():
    """Run comprehensive analysis for multiple symbols"""
    
    symbols = ["SPY", "AAPL", "TSLA"]
    
    for symbol in symbols:
        try:
            await comprehensive_analysis(symbol)
        except Exception as e:
            print(f"\nError analyzing {symbol}: {str(e)}")
        
        if symbol != symbols[-1]:
            await asyncio.sleep(1)  # Brief pause between symbols


if __name__ == "__main__":
    print("\n🚀 MULTI-TOOL TRADING ANALYSIS SYSTEM")
    print("Combining FVG, Volume Profile, Technical Zones, and ORB Analysis")
    asyncio.run(main())
