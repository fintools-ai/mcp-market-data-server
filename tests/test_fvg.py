"""
Test script for the Fair Value Gap (FVG) analysis tool
"""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.tools.fvg_tool import financial_fvg_analysis

async def test_fvg_analysis():
    """Test FVG analysis with different symbols"""
    
    test_symbols = ["SPY", "AAPL", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"Testing FVG Analysis for {symbol}")
        print('='*60)
        
        try:
            result = await financial_fvg_analysis(symbol)
            
            if result['status'] == 'success':
                print(f"\n✓ Current Price: ${result['current_price']}")
                print(f"✓ Bid/Ask: ${result['current_bid']} / ${result['current_ask']}")
                
                # Show FVGs by timeframe
                for timeframe, data in result['timeframe_data'].items():
                    print(f"\n{timeframe} Timeframe:")
                    print(f"  - Total FVGs: {data['fvg_count']}")
                    
                    if data['gaps']:
                        for i, gap in enumerate(data['gaps'][:3]):  # Show first 3 gaps
                            print(f"\n  Gap {i+1} ({gap['type']}):")
                            print(f"    - Range: ${gap['price_levels']['gap_low']:.2f} - ${gap['price_levels']['gap_high']:.2f}")
                            print(f"    - Size: ${gap['price_levels']['gap_size']:.2f}")
                            print(f"    - Filled: {gap['filled_percentage']:.1f}%")
                            print(f"    - Tests: {gap['price_interaction']['times_tested']}")
                            print(f"    - Age: {gap['age_minutes']} minutes")
                
                # Show nearest gaps
                print("\n\nNearest Gaps:")
                print("Above current price:")
                for gap in result['nearest_gaps']['above_current_price']:
                    print(f"  - ${gap['level']} ({gap['timeframe']}) - {gap['distance']:.2f} away")
                
                print("\nBelow current price:")
                for gap in result['nearest_gaps']['below_current_price']:
                    print(f"  - ${gap['level']} ({gap['timeframe']}) - {gap['distance']:.2f} away")
                
                # Show statistics
                print("\n\nGap Statistics (last 5 days):")
                for tf, stats in result['gap_statistics'].items():
                    print(f"\n{tf}:")
                    print(f"  - Total gaps: {stats['total_gaps']}")
                    print(f"  - Filled: {stats['filled_completely']} ({stats['filled_completely']/stats['total_gaps']*100:.1f}%)" if stats['total_gaps'] > 0 else "  - No gaps")
                    print(f"  - Avg fill time: {stats['avg_fill_time_minutes']} minutes")
                
            else:
                print(f"✗ Error: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Test with detailed output for one symbol
    print(f"\n\n{'='*60}")
    print("Detailed JSON output for SPY:")
    print('='*60)
    
    result = await financial_fvg_analysis("SPY")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("Fair Value Gap Analysis Test")
    print("=" * 60)
    asyncio.run(test_fvg_analysis())
