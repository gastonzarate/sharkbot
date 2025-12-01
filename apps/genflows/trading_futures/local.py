import asyncio
import sys
from pathlib import Path

from langfuse import get_client
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.genflows.trading_futures.workflow import TradingFuturesWorkflow  # noqa: E402


async def main():
    # Langfuse configuration
    LlamaIndexInstrumentor().instrument()
    langfuse = get_client()
    trace_id = langfuse.create_trace_id()
    # pylint: disable=not-context-manager
    with langfuse.start_as_current_span(name="trading-futures-workflow", trace_context={"trace_id": trace_id}):
        langfuse.update_current_trace(user_id="test", session_id="test")

        workflow = TradingFuturesWorkflow(timeout=180)
        # Pass the list of currencies you want to trade
        await workflow.run(currencies=["BTC", "ETH"])
    langfuse.flush()


if __name__ == "__main__":
    asyncio.run(main())
