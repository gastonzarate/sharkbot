import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TradingsConfig(AppConfig):
    name = "tradings"
    label = "tradings"  # Django uses this as the app label
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Initialize APScheduler when Django starts.
        This will run the trading workflow every minute.
        """
        # Import here to avoid AppRegistryNotReady exception
        # Only run scheduler in the main process (not in runserver reloader)
        import os
        from django.conf import settings

        from apscheduler.schedulers.background import BackgroundScheduler

        # Prevent scheduler from starting twice in Django's development server
        # The reloader creates a parent process that we don't want to run the scheduler in
        if os.environ.get("RUN_MAIN") != "true":
            logger.info("⏭️  Skipping scheduler initialization (not in main process)")
            return

        # if settings.DEBUG:
        #     return

        from apps.tradings.scheduler import run_trading_workflow

        scheduler = BackgroundScheduler()

        # Schedule the trading workflow to run every custom minutes
        from datetime import datetime, timezone
        
        minutes = 5  # Increased from 1 to ensure workflow completes before next run
        scheduler.add_job(
            run_trading_workflow,
            "interval",
            minutes=minutes,
            id="trading_futures_workflow",
            name="Trading Futures Workflow",
            replace_existing=True,
            misfire_grace_time=30,  # Allow 30s grace for missed executions
            coalesce=True,  # Combine missed executions into one
            max_instances=1,  # Only one instance at a time
            next_run_time=datetime.now(timezone.utc),  # Execute immediately on startup
        )

        scheduler.start()
        logger.info(f"✅ APScheduler started - Trading workflow will run every {minutes} minutes")

        # Shutdown scheduler when Django exits
        import atexit

        atexit.register(lambda: scheduler.shutdown())
