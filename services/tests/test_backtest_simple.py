"""
Simple test script for BacktestService.
Run with: python test_backtest_simple.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from services.binance_client import BinanceClient
from services.backtest_service import BacktestService


def test_backtest():
    """Test BacktestService with real BTC data."""
    
    print("=" * 80)
    print("TESTING BACKTEST SERVICE")
    print("=" * 80)
    
    # Initialize clients
    print("\n1️⃣  Initializing Binance client...")
    client = BinanceClient()
    backtest = BacktestService(client)
    print("   ✅ Clients initialized")
    
    # Get current market data
    print("\n2️⃣  Fetching current BTC market data...")
    market_data = client.get_market_data("BTC")
    print(f"   Current Price: ${market_data['current_price']:,.2f}")
    print(f"   RSI(7): {market_data['current_rsi_short']:.2f}")
    print(f"   MACD: {market_data['current_macd']:.2f}")
    print(f"   EMA(9): ${market_data['current_ema_fast']:,.2f}")
    print(f"   Funding Rate: {market_data['funding_rate']:.4f}%")
    
    # Prepare conditions
    current_conditions = {
        "rsi": market_data["current_rsi_short"],
        "macd": market_data["current_macd"],
        "price": market_data["current_price"],
        "ema_9": market_data["current_ema_fast"],
        "funding_rate": market_data["funding_rate"],
    }
    
    # Test LONG strategy
    print("\n3️⃣  Running backtest for LONG strategy...")
    print("   Analyzing last 7 days of data...")
    
    result = backtest.backtest_strategy(
        currency="BTC",
        direction="LONG",
        current_conditions=current_conditions,
        lookback_days=7,
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
    )
    
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS - LONG STRATEGY")
    print("=" * 80)
    print(f"Direction: {result.get('direction', 'N/A')}")
    print(f"Similar setups found: {result.get('similar_setups_found', 0)}")
    print(f"Trades simulated: {result.get('trades_simulated', 0)}")
    
    if result.get("trades_simulated", 0) > 0:
        print(f"\n📊 Performance Metrics:")
        print(f"   Win Rate: {result['win_rate']}%")
        print(f"   Average Profit: {result['avg_profit_pct']}%")
        print(f"   Average Win: {result['avg_win_pct']}%")
        print(f"   Average Loss: {result['avg_loss_pct']}%")
        print(f"   Max Win: {result['max_win_pct']}%")
        print(f"   Max Loss: {result['max_loss_pct']}%")
        print(f"   Profit Factor: {result['profit_factor']}")
        print(f"   Expectancy: {result['expectancy']}%")
        print(f"   Avg Holding Time: {result['avg_holding_hours']:.1f} hours")
        
        print(f"\n🎯 Outcome Breakdown:")
        outcomes = result['outcome_breakdown']
        print(f"   Take Profit hits: {outcomes['take_profit']}")
        print(f"   Stop Loss hits: {outcomes['stop_loss']}")
        print(f"   Timeouts: {outcomes['timeout']}")
        
        # Recommendation
        print(f"\n💡 Recommendation:")
        if result['expectancy'] > 0 and result['win_rate'] >= 50:
            print("   ✅ Condiciones favorables - estrategia históricamente rentable")
        elif result['expectancy'] > 0:
            print("   ⚠️  Expectativa positiva pero win rate bajo - proceder con precaución")
        else:
            print("   ❌ Expectativa negativa - NO recomendado operar")
    else:
        print("\n⚠️  No se encontraron condiciones similares suficientes para simular trades")
        if result.get("similar_setups_found", 0) > 0:
            print(f"   Se encontraron {result['similar_setups_found']} setups similares")
            print("   pero no hubo datos suficientes después para simular trades completos")
    
    # Test SHORT strategy for comparison
    print("\n" + "=" * 80)
    print("4️⃣  Running backtest for SHORT strategy (for comparison)...")
    
    result_short = backtest.backtest_strategy(
        currency="BTC",
        direction="SHORT",
        current_conditions=current_conditions,
        lookback_days=7,
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
    )
    
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS - SHORT STRATEGY")
    print("=" * 80)
    print(f"Similar setups found: {result_short.get('similar_setups_found', 0)}")
    print(f"Trades simulated: {result_short.get('trades_simulated', 0)}")
    
    if result_short.get("trades_simulated", 0) > 0:
        print(f"Win Rate: {result_short['win_rate']}%")
        print(f"Expectancy: {result_short['expectancy']}%")
        print(f"Profit Factor: {result_short['profit_factor']}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_backtest()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
