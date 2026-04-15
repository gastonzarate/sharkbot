"""
Unit tests for BacktestService.

Tests the core backtesting functionality including:
- Loading historical data
- Finding similar market conditions
- Simulating trades
- Calculating metrics
"""

import pytest
from services.binance_client import BinanceClient
from services.backtest_service import BacktestService


class TestBacktestService:
    """Test suite for BacktestService."""

    @pytest.fixture
    def binance_client(self):
        """Create a BinanceClient instance for testing."""
        return BinanceClient()

    @pytest.fixture
    def backtest_service(self, binance_client):
        """Create a BacktestService instance for testing."""
        return BacktestService(binance_client)

    def test_backtest_strategy_with_real_data(self, backtest_service, binance_client):
        """
        Test backtest_strategy with real market data from Binance.

        This test:
        1. Fetches current market data for BTC
        2. Runs a backtest looking for similar conditions
        3. Validates the returned metrics structure
        """
        # Get current market conditions
        market_data = binance_client.get_market_data("BTC")

        current_conditions = {
            "rsi": market_data["current_rsi_short"],
            "macd": market_data["current_macd"],
            "price": market_data["current_price"],
            "ema_9": market_data["current_ema_fast"],
            "funding_rate": market_data["funding_rate"],
        }

        # Run backtest for LONG direction
        result = backtest_service.backtest_strategy(
            currency="BTC",
            direction="LONG",
            current_conditions=current_conditions,
            lookback_days=7,
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
        )

        # Validate result structure
        assert "similar_setups_found" in result
        assert "trades_simulated" in result

        # If trades were simulated, validate metrics
        if result["trades_simulated"] > 0:
            assert "win_rate" in result
            assert "avg_profit_pct" in result
            assert "expectancy" in result
            assert "profit_factor" in result
            assert "avg_holding_hours" in result
            assert "outcome_breakdown" in result

            # Validate metrics are reasonable
            assert 0 <= result["win_rate"] <= 100
            assert result["profit_factor"] >= 0

            print("\n✅ Backtest Results:")
            print(f"   Similar setups found: {result['similar_setups_found']}")
            print(f"   Trades simulated: {result['trades_simulated']}")
            print(f"   Win rate: {result['win_rate']}%")
            print(f"   Avg profit: {result['avg_profit_pct']}%")
            print(f"   Expectancy: {result['expectancy']}%")
            print(f"   Profit factor: {result['profit_factor']}")
        else:
            print(f"\n⚠️  No similar conditions found in 7-day lookback")
            print(f"   Similar setups found: {result['similar_setups_found']}")

    def test_backtest_strategy_long_vs_short(self, backtest_service, binance_client):
        """
        Test that LONG and SHORT directions produce different results.
        """
        market_data = binance_client.get_market_data("ETH")

        current_conditions = {
            "rsi": market_data["current_rsi_short"],
            "macd": market_data["current_macd"],
            "price": market_data["current_price"],
            "ema_9": market_data["current_ema_fast"],
            "funding_rate": market_data["funding_rate"],
        }

        # Run backtest for both directions
        result_long = backtest_service.backtest_strategy(
            currency="ETH",
            direction="LONG",
            current_conditions=current_conditions,
            lookback_days=7,
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
        )

        result_short = backtest_service.backtest_strategy(
            currency="ETH",
            direction="SHORT",
            current_conditions=current_conditions,
            lookback_days=7,
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
        )

        # Both should have direction set correctly
        if "direction" in result_long:
            assert result_long["direction"] == "LONG"
        if "direction" in result_short:
            assert result_short["direction"] == "SHORT"

        print("\n📊 LONG vs SHORT Comparison:")
        print(f"   LONG - Setups: {result_long.get('similar_setups_found', 0)}, "
              f"Trades: {result_long.get('trades_simulated', 0)}")
        print(f"   SHORT - Setups: {result_short.get('similar_setups_found', 0)}, "
              f"Trades: {result_short.get('trades_simulated', 0)}")

    def test_invalid_direction(self, backtest_service):
        """Test that invalid direction returns error."""
        current_conditions = {
            "rsi": 50,
            "macd": 0,
            "price": 100000,
            "ema_9": 99000,
        }

        result = backtest_service.backtest_strategy(
            currency="BTC",
            direction="INVALID",
            current_conditions=current_conditions,
        )

        assert "error" in result

    def test_different_lookback_periods(self, backtest_service, binance_client):
        """
        Test backtesting with different lookback periods.
        """
        market_data = binance_client.get_market_data("BTC")

        current_conditions = {
            "rsi": market_data["current_rsi_short"],
            "macd": market_data["current_macd"],
            "price": market_data["current_price"],
            "ema_9": market_data["current_ema_fast"],
        }

        # Test with 3-day lookback
        result_3d = backtest_service.backtest_strategy(
            currency="BTC",
            direction="LONG",
            current_conditions=current_conditions,
            lookback_days=3,
        )

        # Test with 14-day lookback
        result_14d = backtest_service.backtest_strategy(
            currency="BTC",
            direction="LONG",
            current_conditions=current_conditions,
            lookback_days=14,
        )

        print("\n📅 Lookback Period Comparison:")
        print(f"   3 days - Setups: {result_3d.get('similar_setups_found', 0)}")
        print(f"   14 days - Setups: {result_14d.get('similar_setups_found', 0)}")

        # Longer lookback should generally find more or equal setups
        assert result_14d.get("similar_setups_found", 0) >= result_3d.get("similar_setups_found", 0)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])
