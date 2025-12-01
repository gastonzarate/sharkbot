import os
import sys
import time

from dotenv import load_dotenv

from services.binance_client import BinanceClient

# Add the current directory to sys.path to make services importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def get_min_quantity(client, symbol):
    """
    Fetch the minimum quantity allowed for the symbol, accounting for MIN_NOTIONAL.
    """
    info = client.client.futures_exchange_info()
    min_qty = 0.001
    min_notional = 100  # Default minimum notional in USDT
    step_size = 0.001

    for s in info["symbols"]:
        if s["symbol"] == symbol:
            for filter in s["filters"]:
                if filter["filterType"] == "LOT_SIZE":
                    min_qty = float(filter["minQty"])
                    step_size = float(filter["stepSize"])
                elif filter["filterType"] == "MIN_NOTIONAL":
                    min_notional = float(filter["notional"])

    # Get current price
    ticker = client.client.get_symbol_ticker(symbol=symbol)
    current_price = float(ticker["price"])

    # Calculate quantity needed to meet min_notional
    qty_for_notional = min_notional / current_price

    # Use the larger of min_qty or qty_for_notional
    required_qty = max(min_qty, qty_for_notional)

    # Round up to the nearest step_size
    import math

    required_qty = math.ceil(required_qty / step_size) * step_size

    return required_qty


def main():
    load_dotenv()

    print("WARNING: This script will execute REAL TRADES.")
    print("You have 5 seconds to cancel (Ctrl+C)...")
    time.sleep(5)

    try:
        client = BinanceClient()
        currency = "BTC"
        symbol = f"{currency}USDT"

        # 1. Check for existing position
        initial_pos = client.get_open_position(currency)
        if initial_pos != 0:
            print(f"ABORTING: You already have an open position of {initial_pos} {currency}.")
            return

        # 2. Get Min Quantity
        min_qty = get_min_quantity(client, symbol)
        print(f"Minimum quantity for {symbol}: {min_qty}")

        # 3. Open Long
        print(f"Opening Long Position ({min_qty} {currency})...")
        order = client.open_long_position(currency, min_qty)
        print(f"Order Placed: {order.get('orderId', 'Error')}")

        # 4. Wait
        print("Waiting 5 seconds...")
        time.sleep(5)

        # 5. Verify Position
        current_pos = client.get_open_position(currency)
        print(f"Current Position: {current_pos}")

        if current_pos == 0:
            print("ERROR: Position was not opened (maybe insufficient funds or margin?).")
            return

        # 5.5. Verify with get_all_open_positions
        print("\nFetching all open positions...")
        all_positions = client.get_all_open_positions()
        print(f"Found {len(all_positions)} open position(s):")
        for pos in all_positions:
            print(f"  - {pos['symbol']}: {pos['side']} {pos['position_amount']} @ ${pos['entry_price']:.2f}")
            print(f"    Unrealized PnL: ${pos['unrealized_pnl']:.2f}, Leverage: {pos['leverage']}x")
        print()

        # 6. Close Position
        print("Closing Position...")
        client.close_position(currency)

        # 7. Verify Closed
        time.sleep(2)
        final_pos = client.get_open_position(currency)
        print(f"Final Position: {final_pos}")

        if final_pos == 0:
            print("SUCCESS: Position opened and closed successfully.")
        else:
            print("WARNING: Position might not be fully closed!")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
