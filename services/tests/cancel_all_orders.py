import os
import sys

from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from services.binance_client import BinanceClient


def main():
    load_dotenv()

    try:
        client = BinanceClient()
        print("=" * 60)
        print("CANCELLING ALL OPEN FUTURES ORDERS")
        print("=" * 60 + "\n")

        # Cancel all open orders
        result = client.cancel_all_open_orders()

        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print("=" * 60)
        print(f"Total orders cancelled: {result['cancelled_count']}")

        if result.get("error"):
            print(f"Error: {result['error']}")
        elif result["cancelled_count"] > 0:
            print("\nCancelled orders by symbol:")
            for order in result["orders"]:
                print(f"  - {order['symbol']}")
        else:
            print("\nNo open orders found.")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
