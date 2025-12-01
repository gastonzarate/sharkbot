from llama_index.utils.workflow import draw_all_possible_flows

from apps.genflows.trading_futures.workflow import TradingFuturesWorkflow

# To run python -m apps.genflows.trading_futures.draw
draw_all_possible_flows(
    TradingFuturesWorkflow, filename="apps/genflows/trading_futures/trading_futures_workflow_all.html"
)
