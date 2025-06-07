#!/usr/bin/env python3
"""
Test script for ORB (Opening Range Breakout) tool
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.tools.orb_tool import financial_orb_analysis

async def test_orb():
    """Test the ORB analysis tool"""
    
    print("🎯 Testing ORB Analysis Tool")
    print("=" * 50)
    
    # Test symbols
    test_symbols = ["SPY", "QQQ", "AAPL"]
    
    for symbol in test_symbols:
        print(f"\n📊 Analyzing ORB for {symbol}...")
        
        try:
            # Call the ORB analysis function
            result = await financial_orb_analysis(symbol)
            print(result)
            
            if result['status'] == 'success':
                print(f"✅ Success for {symbol}")
                
                # Display ORB analysis for each period
                orb_data = result.get('orb_analysis', {})
                
                for period, data in orb_data.items():
                    if isinstance(data, dict) and data.get('status') != 'insufficient_data':
                        print(f"\n  {period} ORB:")
                        print(f"    Range: ${data['orb_low']:.2f} - ${data['orb_high']:.2f} (${data['orb_range']:.2f})")
                        print(f"    Current: ${data['current_price']:.2f} ({data['position']})")
                        
                        if data['breakout_confirmed']:
                            print(f"    🚀 {data['breakout_type'].upper()} breakout confirmed!")
                        
                        if data['volume_analysis']['high_volume']:
                            print(f"    📈 High volume detected (ratio: {data['volume_analysis']['volume_ratio_vs_day_avg']:.2f}x)")
                        
                        if data['targets_hit']:
                            print(f"    🎯 Targets hit: {', '.join(data['targets_hit'])}")
                
                # Display trading bias
                bias = result.get('trading_bias', {})
                if bias:
                    print(f"\n  Overall Bias: {bias['bias'].upper()} (confidence: {bias['confidence']})")
                    if bias['strength_factors']:
                        print(f"  Factors: {', '.join(bias['strength_factors'][:3])}")
                
                # Check for ORB squeeze
                squeeze = result.get('orb_squeeze', {})
                if squeeze.get('squeeze_detected'):
                    print(f"\n  ⚠️  ORB SQUEEZE DETECTED! Compression ratio: {squeeze['compression_ratio']:.2f}")
                
            else:
                print(f"❌ Error for {symbol}: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception for {symbol}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ ORB test completed!")

if __name__ == "__main__":
    asyncio.run(test_orb())
