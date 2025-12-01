import os
import sys

from dotenv import load_dotenv

from services.binance_client import BinanceClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    load_dotenv()

    try:
        client = BinanceClient()
        print("Fetching Futures Account Balance...\n")

        balance = client.get_futures_balance()

        print("=== ACCOUNT SUMMARY ===")
        print(f"Total Wallet Balance: ${balance['total_wallet_balance']:.2f}")
        print(f"Total Margin Balance: ${balance['total_margin_balance']:.2f}")
        print(f"Available Balance: ${balance['available_balance']:.2f}")
        print(f"Total Unrealized PnL: ${balance['total_unrealized_pnl']:.2f}")

        print("\n=== ASSETS ===")
        if balance["assets"]:
            for asset in balance["assets"]:
                print(f"\n{asset['asset']}:")
                print(f"  Wallet Balance: {asset['wallet_balance']:.8f}")
                print(f"  Available Balance: {asset['available_balance']:.8f}")
                print(f"  Margin Balance: {asset['margin_balance']:.8f}")
                print(f"  Unrealized Profit: {asset['unrealized_profit']:.8f}")
        else:
            print("No assets with balance found.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
