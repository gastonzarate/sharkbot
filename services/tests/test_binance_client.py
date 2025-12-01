from services.binance_client import BinanceClient

try:
    client = BinanceClient()
    print("BinanceClient initialized successfully.")

    currency = "BTC"
    print(f"Fetching data for {currency}...")
    data = client.get_market_data(currency)

    print("\n### Data Fetched Successfully ###\n")
    for key, value in data.items():
        print(f"{key}: {value}")

except Exception as e:
    print(f"An error occurred: {e}")
