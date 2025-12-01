import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from dotenv import load_dotenv

from services.binance_client import BinanceClient


def main():
    load_dotenv()

    try:
        client = BinanceClient()
        print("Fetching available Futures symbols...\n")

        symbols = client.get_available_futures_symbols(quote_asset="USDT")

        print(f"Found {len(symbols)} USDT perpetual futures contracts:\n")

        # Display first 20 symbols
        print("First 20 symbols:")
        for i, symbol_info in enumerate(symbols[:20], 1):
            print(
                f"{i:2d}. {symbol_info['symbol']:15s} - {symbol_info['base_asset']:10s} (Price: {symbol_info['price_precision']} decimals, Qty: {symbol_info['quantity_precision']} decimals)"
            )

        if len(symbols) > 20:
            print(f"\n... and {len(symbols) - 20} more symbols")

        # Show some popular ones
        popular = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]
        print("\n\nPopular symbols:")
        for pop in popular:
            found = next((s for s in symbols if s["symbol"] == pop), None)
            if found:
                print(f"  {found['symbol']:15s} - {found['base_asset']:10s}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
