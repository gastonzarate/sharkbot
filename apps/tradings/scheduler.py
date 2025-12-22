import asyncio
import logging
import time

import nest_asyncio
from langfuse import get_client
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from tradings.models import TradingWorkflowExecution

from apps.genflows.trading_futures.workflow import TradingFuturesWorkflow

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

logger = logging.getLogger(__name__)


async def execute_workflow():
    """
    Run the trading workflow inside an active event loop.
    The workflow's .run() method is synchronous and schedules tasks using
    asyncio.create_task(), so it must be invoked from within a running loop.
    """
    LlamaIndexInstrumentor().instrument()
    langfuse = get_client()
    trace_id = langfuse.create_trace_id()
    # pylint: disable=not-context-manager
    with langfuse.start_as_current_span(
        name="trading-futures-workflow-scheduled", trace_context={"trace_id": trace_id}
    ):
        langfuse.update_current_trace(user_id="scheduler", session_id=f"scheduled-{trace_id}")

        workflow = TradingFuturesWorkflow(timeout=480)
        logger.info("✅ Trading workflow initialized")

        handler = workflow.run(currencies=["BTC", "ETH", "BFUSD", "BNB", "USDC"])
    langfuse.flush()

    return await handler


def run_trading_workflow():
    """
    Execute the trading futures workflow.
    This function runs every minute via APScheduler.
    """

    start_time = time.time()
    result = None
    error = None

    try:
        # Create and run the workflow within a running event loop
        result = asyncio.run(execute_workflow())

    except Exception as e:
        error = e
        logger.error(f"❌ Error executing trading workflow: {e}", exc_info=True)

    finally:
        # Calculate execution duration
        execution_duration = time.time() - start_time

        # Save to database
        try:
            if result:
                execution = TradingWorkflowExecution.save_from_workflow_result(
                    result=result, execution_duration=execution_duration, error=error
                )
                logger.info(
                    f"💾 Execution saved to database: {execution.id} - "
                    f"Status: {execution.status} - Duration: {execution_duration:.2f}s"
                )
            elif error:
                # Save error-only execution
                execution = TradingWorkflowExecution(
                    status=TradingWorkflowExecution.Status.ERROR,
                    execution_duration=execution_duration,
                    currencies=[],
                    balance_info={},
                    market_data={},
                    open_positions=[],
                    daily_pnl={},
                    system_prompt="",
                    error_message=str(error),
                )
                execution.save()
                logger.error(f"💾 Error execution saved to database: {execution.id}")
        except Exception as db_error:
            logger.error(f"❌ Failed to save execution to database: {db_error}", exc_info=True)

        logger.info("✅ Trading workflow execution finished")
