import os

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange


class BinanceClient:
    def __init__(self):
        """
        Initialize the Binance Client using environment variables.
        """
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set in environment variables.")

        self.client = Client(api_key, api_secret)

    def get_market_data(self, currency: str) -> dict:
        """
        Fetch and aggregate market data for a given currency.

        Args:
            currency (str): The currency symbol (e.g., 'BTC').

        Returns:
            dict: A dictionary containing the aggregated market data.
        """
        symbol = f"{currency.upper()}USDT"

        # 1. Fetch Current Snapshot
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker["price"])

        # Fetch recent klines for current indicators (using 1h interval for "current" context)
        # We need enough data for EMA(9), MACD(26, 12, 9), RSI(7)
        klines_1h = self._get_klines(symbol, Client.KLINE_INTERVAL_1HOUR, limit=100)
        df_1h = self._calculate_indicators(klines_1h)

        current_ema_9 = df_1h["ema_9"].iloc[-1]
        current_macd = df_1h["macd"].iloc[-1]
        current_rsi_7 = df_1h["rsi_7"].iloc[-1]

        # 2. Fetch Perpetual Futures Metrics
        futures_metrics = self._get_futures_metrics(symbol)

        # 3. Intraday Series (1h interval)
        # We want the series data. Let's take the last 10 points for the "series" display.
        series_length = 10
        intraday_series = {
            "prices": df_1h["close"].tail(series_length).tolist(),
            "ema_9": df_1h["ema_9"].tail(series_length).tolist(),
            "macd": df_1h["macd"].tail(series_length).tolist(),
            "rsi_7": df_1h["rsi_7"].tail(series_length).tolist(),
            "rsi_14": df_1h["rsi_14"].tail(series_length).tolist(),
        }

        # 4. Longer-term Context (1d interval)
        klines_1d = self._get_klines(symbol, Client.KLINE_INTERVAL_1DAY, limit=100)
        df_1d = self._calculate_indicators(klines_1d)

        current_vol = df_1d["volume"].iloc[-1]
        avg_vol = df_1d["volume"].mean()  # Simple average of the fetched period

        long_term_context = {
            "ema_9": df_1d["ema_9"].iloc[-1],
            "ema_21": df_1d["ema_21"].iloc[-1],
            "atr_14": df_1d["atr_14"].iloc[-1],
            "atr_28": df_1d["atr_28"].iloc[-1],
            "current_volume": current_vol,
            "average_volume": avg_vol,
            "macd_series": df_1d["macd"].tail(series_length).tolist(),
            "rsi_14_series": df_1d["rsi_14"].tail(series_length).tolist(),
        }

        # Construct the final dictionary
        return {
            "current_price": current_price,
            "current_ema_fast": current_ema_9,
            "current_macd": current_macd,
            "current_rsi_short": current_rsi_7,
            "oi_latest": futures_metrics["oi_latest"],
            "oi_average": futures_metrics["oi_average"],
            "funding_rate": futures_metrics["funding_rate"],
            "intraday_interval_label": "1H",
            "mid_prices": intraday_series["prices"],
            "ema_series": intraday_series["ema_9"],
            "macd_series": intraday_series["macd"],
            "rsi_short_series": intraday_series["rsi_7"],
            "rsi_long_series": intraday_series["rsi_14"],
            "long_tf_label": "1D",
            "ema_fast_long": long_term_context["ema_9"],
            "ema_slow_long": long_term_context["ema_21"],
            "atr_fast": long_term_context["atr_14"],
            "atr_slow": long_term_context["atr_28"],
            "current_volume": long_term_context["current_volume"],
            "average_volume": long_term_context["average_volume"],
            "macd_long_series": long_term_context["macd_series"],
            "rsi_long_series_longtf": long_term_context["rsi_14_series"],
        }

    def _get_klines(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        """
        Fetch historical klines and return as a DataFrame.
        """
        klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(
            klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )

        # Convert numeric columns
        numeric_cols = ["open", "high", "low", "close", "volume"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)

        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators (EMA, MACD, RSI, ATR).
        """
        # EMA
        df["ema_9"] = EMAIndicator(close=df["close"], window=9).ema_indicator()
        df["ema_21"] = EMAIndicator(close=df["close"], window=21).ema_indicator()

        # MACD (12, 26, 9)
        macd = MACD(close=df["close"])
        df["macd"] = macd.macd()

        # RSI
        df["rsi_7"] = RSIIndicator(close=df["close"], window=7).rsi()
        df["rsi_14"] = RSIIndicator(close=df["close"], window=14).rsi()

        # ATR
        atr_14 = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14)
        df["atr_14"] = atr_14.average_true_range()

        atr_28 = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=28)
        df["atr_28"] = atr_28.average_true_range()

        return df

    def _get_futures_metrics(self, symbol: str) -> dict:
        """
        Fetch Futures Open Interest and Funding Rate.
        """
        try:
            # Open Interest
            # Fetching Open Interest Statistics (last 24 hours)
            oi_stats = self.client.futures_open_interest_hist(symbol=symbol, period="1h", limit=24)

            if not oi_stats:
                return {"oi_latest": 0, "oi_average": 0, "funding_rate": 0}

            latest_oi = float(oi_stats[-1]["sumOpenInterest"])
            avg_oi = sum(float(x["sumOpenInterest"]) for x in oi_stats) / len(oi_stats)

            # Funding Rate
            funding_rate_info = self.client.futures_funding_rate(symbol=symbol, limit=1)
            funding_rate = float(funding_rate_info[-1]["fundingRate"]) * 100 if funding_rate_info else 0.0

            return {"oi_latest": latest_oi, "oi_average": avg_oi, "funding_rate": funding_rate}

        except BinanceAPIException as e:
            print(f"Error fetching futures metrics: {e}")
            return {"oi_latest": 0, "oi_average": 0, "funding_rate": 0}

    def set_leverage(self, currency: str, leverage: int) -> bool:
        """
        Set leverage for a symbol.

        Args:
            currency (str): The currency symbol (e.g., 'BTC').
            leverage (int): Leverage value (1-125 depending on symbol).

        Returns:
            bool: True if successful, False otherwise.
        """
        symbol = f"{currency.upper()}USDT"
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            print(f"Leverage set to {leverage}x for {symbol}")
            return True
        except BinanceAPIException as e:
            print(f"Error setting leverage: {e}")
            return False

    def _place_stop_loss(self, symbol: str, side: str, quantity: float, stop_price: float) -> dict:
        """
        Place a Stop Loss order.

        Args:
            symbol: Trading pair symbol
            side: 'SELL' for long positions, 'BUY' for short positions
            quantity: Position quantity
            stop_price: Stop loss trigger price
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="STOP_MARKET",
                stopPrice=stop_price,
                quantity=quantity,
                closePosition=False,
            )
            print(f"Stop Loss placed at ${stop_price:.2f}")
            return order
        except BinanceAPIException as e:
            print(f"Error placing Stop Loss: {e}")
            return {"error": str(e)}

    def _place_take_profit(self, symbol: str, side: str, quantity: float, tp_price: float) -> dict:
        """
        Place a Take Profit order.

        Args:
            symbol: Trading pair symbol
            side: 'SELL' for long positions, 'BUY' for short positions
            quantity: Position quantity
            tp_price: Take profit trigger price
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp_price,
                quantity=quantity,
                closePosition=False,
            )
            print(f"Take Profit placed at ${tp_price:.2f}")
            return order
        except BinanceAPIException as e:
            print(f"Error placing Take Profit: {e}")
            return {"error": str(e)}

    def open_long_position(
        self,
        currency: str,
        quantity: float,
        stop_loss_price: float = None,
        take_profit_price: float = None,
        leverage: int = None,
    ) -> dict:
        """
        Open a Long position with mandatory Stop Loss and optional Take Profit.

        Args:
            currency (str): The currency symbol (e.g., 'BTC').
            quantity (float): The quantity to buy.
            stop_loss_price (float): Stop loss trigger price (REQUIRED).
            take_profit_price (float, optional): Take profit trigger price.
            leverage (int, optional): Leverage to use (1-125).

        Returns:
            dict: Summary with main order and SL/TP order IDs.

        Raises:
            ValueError: If stop_loss_price is not provided.
        """
        # Validate that stop loss is provided
        if stop_loss_price is None:
            raise ValueError("stop_loss_price is required. Cannot open a long position without a stop loss.")

        symbol = f"{currency.upper()}USDT"

        # Set leverage if specified
        if leverage:
            self.set_leverage(currency, leverage)

        # Open main position
        main_order = self._place_order(symbol, Client.SIDE_BUY, quantity, Client.ORDER_TYPE_MARKET)

        if "error" in main_order:
            return main_order

        result = {"main_order_id": main_order.get("orderId"), "symbol": symbol, "side": "LONG", "quantity": quantity}

        # Place Stop Loss (now mandatory)
        sl_order = self._place_stop_loss(symbol, Client.SIDE_SELL, quantity, stop_loss_price)
        result["stop_loss_order_id"] = sl_order.get("orderId")
        result["stop_loss_price"] = stop_loss_price

        # Place Take Profit if specified
        if take_profit_price:
            tp_order = self._place_take_profit(symbol, Client.SIDE_SELL, quantity, take_profit_price)
            result["take_profit_order_id"] = tp_order.get("orderId")
            result["take_profit_price"] = take_profit_price

        return result

    def open_short_position(
        self,
        currency: str,
        quantity: float,
        stop_loss_price: float = None,
        take_profit_price: float = None,
        leverage: int = None,
    ) -> dict:
        """
        Open a Short position with mandatory Stop Loss and optional Take Profit.

        Args:
            currency (str): The currency symbol (e.g., 'BTC').
            quantity (float): The quantity to sell.
            stop_loss_price (float): Stop loss trigger price (REQUIRED).
            take_profit_price (float, optional): Take profit trigger price.
            leverage (int, optional): Leverage to use (1-125).

        Returns:
            dict: Summary with main order and SL/TP order IDs.

        Raises:
            ValueError: If stop_loss_price is not provided.
        """
        # Validate that stop loss is provided
        if stop_loss_price is None:
            raise ValueError("stop_loss_price is required. Cannot open a short position without a stop loss.")

        symbol = f"{currency.upper()}USDT"

        # Set leverage if specified
        if leverage:
            self.set_leverage(currency, leverage)

        # Open main position
        main_order = self._place_order(symbol, Client.SIDE_SELL, quantity, Client.ORDER_TYPE_MARKET)

        if "error" in main_order:
            return main_order

        result = {"main_order_id": main_order.get("orderId"), "symbol": symbol, "side": "SHORT", "quantity": quantity}

        # Place Stop Loss (now mandatory)
        sl_order = self._place_stop_loss(symbol, Client.SIDE_BUY, quantity, stop_loss_price)
        result["stop_loss_order_id"] = sl_order.get("orderId")
        result["stop_loss_price"] = stop_loss_price

        # Place Take Profit if specified (BUY for short positions)
        if take_profit_price:
            tp_order = self._place_take_profit(symbol, Client.SIDE_BUY, quantity, take_profit_price)
            result["take_profit_order_id"] = tp_order.get("orderId")
            result["take_profit_price"] = take_profit_price

        return result

    def _place_order(self, symbol: str, side: str, quantity: float, order_type: str) -> dict:
        """
        Helper to place a futures order.
        """
        try:
            print(f"Placing {side} {order_type} order for {quantity} {symbol}...")
            # Note: This executes a REAL order if connected to a live account!
            order = self.client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
            return order
        except BinanceAPIException as e:
            print(f"Error placing order: {e}")
            return {"error": str(e)}

    def get_open_position(self, currency: str) -> float:
        """
        Get the current open position amount for a currency.
        Positive = Long, Negative = Short, 0 = No position.
        """
        symbol = f"{currency.upper()}USDT"
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            for p in positions:
                if p["symbol"] == symbol:
                    return float(p["positionAmt"])
            return 0.0
        except BinanceAPIException as e:
            print(f"Error fetching position: {e}")
            return 0.0

    def close_position(self, currency: str) -> dict:
        """
        Close the current open position for the given currency.
        """
        amount = self.get_open_position(currency)
        if amount == 0:
            print(f"No open position for {currency}.")
            return {"status": "NO_POSITION"}

        symbol = f"{currency.upper()}USDT"
        side = Client.SIDE_SELL if amount > 0 else Client.SIDE_BUY
        quantity = abs(amount)

        print(f"Closing position for {currency}: {side} {quantity}")
        return self._place_order(symbol, side, quantity, Client.ORDER_TYPE_MARKET)

    def get_all_open_positions(self) -> list:
        """
        Get all open futures positions with associated orders and risk metrics.

        Returns:
            list: List of dictionaries with comprehensive position information including:
                  - Position details (amount, entry price, PnL, leverage)
                  - Associated orders (stop-loss, take-profit, limit orders)
                  - Risk metrics (liquidation price, mark price, margin ratio)
        """
        try:
            positions = self.client.futures_position_information()
            # Fetch all open orders once to avoid multiple API calls
            all_orders = self.client.futures_get_open_orders()

            open_positions = []

            for p in positions:
                position_amt = float(p["positionAmt"])
                if position_amt != 0:
                    symbol = p["symbol"]

                    # Filter orders for this symbol
                    symbol_orders = [o for o in all_orders if o["symbol"] == symbol]

                    # Categorize orders by type
                    stop_loss_orders = []
                    take_profit_orders = []
                    limit_orders = []

                    for order in symbol_orders:
                        order_info = {
                            "order_id": order["orderId"],
                            "type": order["type"],
                            "side": order["side"],
                            "price": float(order.get("price", 0)),
                            "stop_price": float(order.get("stopPrice", 0)),
                            "quantity": float(order["origQty"]),
                            "status": order["status"],
                            "time": order["time"],
                        }

                        if order["type"] in ["STOP_MARKET", "STOP"]:
                            stop_loss_orders.append(order_info)
                        elif order["type"] in ["TAKE_PROFIT_MARKET", "TAKE_PROFIT"]:
                            take_profit_orders.append(order_info)
                        elif order["type"] == "LIMIT":
                            limit_orders.append(order_info)

                    # Build comprehensive position info
                    position_info = {
                        "symbol": symbol,
                        "position_amount": position_amt,
                        "entry_price": float(p.get("entryPrice", 0)),
                        "mark_price": float(p.get("markPrice", 0)),
                        "liquidation_price": float(p.get("liquidationPrice", 0)),
                        "unrealized_pnl": float(p.get("unRealizedProfit", 0)),
                        "leverage": int(p.get("leverage", 1)),
                        "side": "LONG" if position_amt > 0 else "SHORT",
                        "margin_type": p.get("marginType", "cross"),
                        "isolated_wallet": float(p.get("isolatedWallet", 0)),
                        "position_initial_margin": float(p.get("positionInitialMargin", 0)),
                        # Associated orders
                        "stop_loss_orders": stop_loss_orders,
                        "take_profit_orders": take_profit_orders,
                        "limit_orders": limit_orders,
                        "total_orders": len(symbol_orders),
                    }

                    open_positions.append(position_info)

            return open_positions
        except BinanceAPIException as e:
            print(f"Error fetching all positions: {e}")
            return []

    def get_futures_balance(self) -> dict:
        """
        Get the futures account balance information.

        Returns:
            dict: Dictionary with balance information including total balance, available balance, and unrealized PnL.
        """
        try:
            account_info = self.client.futures_account()

            # Extract relevant balance information
            total_balance = float(account_info.get("totalWalletBalance", 0))
            available_balance = float(account_info.get("availableBalance", 0))
            total_unrealized_pnl = float(account_info.get("totalUnrealizedProfit", 0))
            total_margin_balance = float(account_info.get("totalMarginBalance", 0))

            # Get individual asset balances
            assets = []
            for asset in account_info.get("assets", []):
                wallet_balance = float(asset.get("walletBalance", 0))
                if wallet_balance > 0:  # Only include assets with balance
                    assets.append(
                        {
                            "asset": asset.get("asset"),
                            "wallet_balance": wallet_balance,
                            "unrealized_profit": float(asset.get("unrealizedProfit", 0)),
                            "margin_balance": float(asset.get("marginBalance", 0)),
                            "available_balance": float(asset.get("availableBalance", 0)),
                        }
                    )

            return {
                "total_wallet_balance": total_balance,
                "total_margin_balance": total_margin_balance,
                "available_balance": available_balance,
                "total_unrealized_pnl": total_unrealized_pnl,
                "assets": assets,
            }
        except BinanceAPIException as e:
            print(f"Error fetching futures balance: {e}")
            return {
                "total_wallet_balance": 0,
                "total_margin_balance": 0,
                "available_balance": 0,
                "total_unrealized_pnl": 0,
                "assets": [],
            }

    def get_available_futures_symbols(self, quote_asset: str = "USDT") -> list:
        """
        Get all available futures trading symbols.

        Args:
            quote_asset (str): Filter by quote asset (default: 'USDT').

        Returns:
            list: List of dictionaries with symbol information.
        """
        try:
            exchange_info = self.client.futures_exchange_info()
            symbols = []

            for symbol_info in exchange_info.get("symbols", []):
                # Filter by quote asset and only include PERPETUAL contracts
                if (
                    symbol_info.get("quoteAsset") == quote_asset
                    and symbol_info.get("contractType") == "PERPETUAL"
                    and symbol_info.get("status") == "TRADING"
                ):

                    symbols.append(
                        {
                            "symbol": symbol_info.get("symbol"),
                            "base_asset": symbol_info.get("baseAsset"),
                            "quote_asset": symbol_info.get("quoteAsset"),
                            "price_precision": symbol_info.get("pricePrecision"),
                            "quantity_precision": symbol_info.get("quantityPrecision"),
                        }
                    )

            return sorted(symbols, key=lambda x: x["symbol"])

        except BinanceAPIException as e:
            print(f"Error fetching futures symbols: {e}")
            return []

    def cancel_all_open_orders(self, symbol: str = None) -> dict:
        """
        Cancel all open orders for futures.

        Args:
            symbol (str, optional): If provided, only cancel orders for this symbol.
                                   If None, cancel all orders for all symbols.

        Returns:
            dict: Summary of cancelled orders.
        """
        try:
            cancelled_orders = []

            if symbol:
                # Cancel orders for specific symbol
                result = self.client.futures_cancel_all_open_orders(symbol=symbol)
                cancelled_orders.append({"symbol": symbol, "result": result})
                print(f"✓ Cancelled all open orders for {symbol}")
            else:
                # Get all open orders first
                all_orders = self.client.futures_get_open_orders()

                if not all_orders:
                    print("No open orders to cancel.")
                    return {"cancelled_count": 0, "orders": []}

                # Group by symbol
                symbols_with_orders = set(order["symbol"] for order in all_orders)

                # Cancel for each symbol
                for sym in symbols_with_orders:
                    result = self.client.futures_cancel_all_open_orders(symbol=sym)
                    cancelled_orders.append({"symbol": sym, "result": result})
                    print(f"✓ Cancelled all open orders for {sym}")

            return {"cancelled_count": len(cancelled_orders), "orders": cancelled_orders}

        except BinanceAPIException as e:
            print(f"Error cancelling orders: {e}")
            return {"error": str(e), "cancelled_count": 0, "orders": []}

    def get_daily_pnl(self, include_unrealized: bool = True) -> dict:
        """
        Get today's realized PnL and trade statistics.

        Args:
            include_unrealized (bool): If True, includes unrealized PnL from open positions 
                                      to match Binance's total daily PnL display (default: True)

        Returns:
            dict: Daily performance metrics including realized PnL, unrealized PnL, 
                  total daily PnL, and trade count.
        """
        try:
            # Get income history (realized PnL)
            income = self.client.futures_income_history(incomeType="REALIZED_PNL", limit=100)

            # Filter today's trades
            from datetime import datetime, timezone

            today_start = (
                datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000
            )

            today_trades = [i for i in income if i["time"] >= today_start]
            today_realized_pnl = sum(float(i["income"]) for i in today_trades)

            # Get unrealized PnL from open positions if requested
            unrealized_pnl = 0
            if include_unrealized:
                balance_info = self.get_futures_balance()
                unrealized_pnl = balance_info.get("total_unrealized_pnl", 0)

            # Calculate total daily PnL (matches Binance's display)
            total_daily_pnl = today_realized_pnl + unrealized_pnl

            # Calculate win rate
            winning_trades = sum(1 for i in today_trades if float(i["income"]) > 0)
            total_trades = len(today_trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            return {
                "daily_realized_pnl": today_realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_daily_pnl": total_daily_pnl,
                "trade_count": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "win_rate": win_rate,
            }
        except BinanceAPIException as e:
            print(f"Error fetching daily PnL: {e}")
            return {
                "daily_realized_pnl": 0,
                "unrealized_pnl": 0,
                "total_daily_pnl": 0,
                "trade_count": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
            }

    def get_recent_trades(self, currency: str, limit: int = 10) -> list:
        """
        Get recent executed trades for a specific currency.

        Args:
            currency (str): The currency symbol (e.g., 'BTC').
            limit (int): Number of recent trades to fetch (default: 10).

        Returns:
            list: Recent trades with execution details and PnL.
        """
        symbol = f"{currency.upper()}USDT"
        try:
            trades = self.client.futures_account_trades(symbol=symbol, limit=limit)

            return [
                {
                    "symbol": t["symbol"],
                    "trade_id": t["id"],
                    "order_id": t["orderId"],
                    "side": t["side"],
                    "price": float(t["price"]),
                    "quantity": float(t["qty"]),
                    "realized_pnl": float(t["realizedPnl"]),
                    "commission": float(t["commission"]),
                    "commission_asset": t["commissionAsset"],
                    "time": t["time"],
                    "is_maker": t["maker"],
                }
                for t in trades
            ]
        except BinanceAPIException as e:
            print(f"Error fetching recent trades for {currency}: {e}")
            return []

    def get_order_book_depth(self, currency: str, limit: int = 10) -> dict:
        """
        Get order book depth for market liquidity analysis.

        Args:
            currency (str): The currency symbol (e.g., 'BTC').
            limit (int): Number of price levels to fetch (default: 10).

        Returns:
            dict: Order book with bid/ask levels and volumes.
        """
        symbol = f"{currency.upper()}USDT"
        try:
            depth = self.client.futures_order_book(symbol=symbol, limit=limit)

            # Calculate total volumes
            bid_volume = sum(float(q) for _, q in depth["bids"])
            ask_volume = sum(float(q) for _, q in depth["asks"])

            # Get top 5 levels for display
            top_bids = [(float(p), float(q)) for p, q in depth["bids"][:5]]
            top_asks = [(float(p), float(q)) for p, q in depth["asks"][:5]]

            # Calculate spread
            best_bid = float(depth["bids"][0][0]) if depth["bids"] else 0
            best_ask = float(depth["asks"][0][0]) if depth["asks"] else 0
            spread = best_ask - best_bid
            spread_percentage = (spread / best_bid * 100) if best_bid > 0 else 0

            return {
                "symbol": symbol,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread": spread,
                "spread_percentage": spread_percentage,
                "top_bids": top_bids,
                "top_asks": top_asks,
                "total_bid_volume": bid_volume,
                "total_ask_volume": ask_volume,
                "bid_ask_ratio": bid_volume / ask_volume if ask_volume > 0 else 0,
            }
        except BinanceAPIException as e:
            print(f"Error fetching order book for {currency}: {e}")
            return {
                "symbol": symbol,
                "best_bid": 0,
                "best_ask": 0,
                "spread": 0,
                "spread_percentage": 0,
                "top_bids": [],
                "top_asks": [],
                "total_bid_volume": 0,
                "total_ask_volume": 0,
                "bid_ask_ratio": 0,
            }
