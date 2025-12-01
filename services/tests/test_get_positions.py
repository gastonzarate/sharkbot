import os
import sys

from dotenv import load_dotenv

from services.binance_client import BinanceClient

# Add the current directory to sys.path to make services importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    load_dotenv()

    try:
        client = BinanceClient()
        print("Fetching all open positions...\n")

        positions = client.get_all_open_positions()

        if not positions:
            print("No open positions found.")
        else:
            print(f"Found {len(positions)} open position(s):\n")
            for pos in positions:
                print(f"Symbol: {pos['symbol']}")
                print(f"  Side: {pos['side']}")
                print(f"  Amount: {pos['position_amount']}")
                print(f"  Entry Price: ${pos['entry_price']:.2f}")
                print(f"  Unrealized PnL: ${pos['unrealized_pnl']:.2f}")
                print(f"  Leverage: {pos['leverage']}x")
                print()

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
