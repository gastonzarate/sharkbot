import os
import sys
import time

from dotenv import load_dotenv

from services.binance_client import BinanceClient

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def get_min_quantity(client, symbol):
    """
    Fetch the minimum quantity allowed for the symbol, accounting for MIN_NOTIONAL.
    """
    info = client.client.futures_exchange_info()
    min_qty = 0.001
    min_notional = 100
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

    return required_qty, current_price


def main():
    load_dotenv()

    print("WARNING: This script will execute REAL TRADES with SL/TP.")
    print("You have 5 seconds to cancel (Ctrl+C)...")
    time.sleep(5)

    try:
        client = BinanceClient()
        currency = "BTC"
        symbol = f"{currency}USDT"

        # Check for existing position
        initial_pos = client.get_open_position(currency)
        if initial_pos != 0:
            print(f"ABORTING: You already have an open position of {initial_pos} {currency}.")
            return

        # Get Min Quantity and current price
        min_qty, current_price = get_min_quantity(client, symbol)
        print(f"Current Price: ${current_price:.2f}")
        print(f"Minimum quantity for {symbol}: {min_qty}")

        # Calculate SL and TP prices (2% SL, 3% TP for long)
        stop_loss = current_price * 0.98  # 2% below entry
        take_profit = current_price * 1.03  # 3% above entry

        print(f"\nOpening Long Position with:")
        print(f"  Quantity: {min_qty} {currency}")
        print(f"  Stop Loss: ${stop_loss:.2f} (-2%)")
        print(f"  Take Profit: ${take_profit:.2f} (+3%)")
        print("  Leverage: 1x")

        # Open Long with SL/TP
        result = client.open_long_position(
            currency=currency, quantity=min_qty, stop_loss_price=stop_loss, take_profit_price=take_profit, leverage=1
        )

        print(f"\n=== ORDER SUMMARY ===")
        print(f"Main Order ID: {result.get('main_order_id')}")
        print(f"Symbol: {result.get('symbol')}")
        print(f"Side: {result.get('side')}")
        print(f"Quantity: {result.get('quantity')}")

        if "stop_loss_order_id" in result:
            print(f"Stop Loss Order ID: {result.get('stop_loss_order_id')}")
            print(f"Stop Loss Price: ${result.get('stop_loss_price'):.2f}")

        if "take_profit_order_id" in result:
            print(f"Take Profit Order ID: {result.get('take_profit_order_id')}")
            print(f"Take Profit Price: ${result.get('take_profit_price'):.2f}")

        # Wait and verify
        print("\nWaiting 3 seconds...")
        time.sleep(3)

        # Check position
        current_pos = client.get_open_position(currency)
        print(f"Current Position: {current_pos}")

        if current_pos == 0:
            print("ERROR: Position was not opened.")
            return

        # Get all positions to verify
        all_positions = client.get_all_open_positions()
        print(f"\nOpen Positions: {len(all_positions)}")
        for pos in all_positions:
            print(f"  {pos['symbol']}: {pos['side']} {pos['position_amount']}")

        # Close position (this will also cancel SL/TP orders)
        print("\nClosing position...")
        client.close_position(currency)

        time.sleep(2)
        final_pos = client.get_open_position(currency)
        print(f"Final Position: {final_pos}")

        if final_pos == 0:
            print("\nSUCCESS: Position with SL/TP opened and closed successfully!")
        else:
            print("\nWARNING: Position might not be fully closed!")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
