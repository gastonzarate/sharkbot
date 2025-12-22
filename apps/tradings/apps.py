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
        from django.conf import settings

        from apscheduler.schedulers.background import BackgroundScheduler

        # if settings.DEBUG:
        #     return

        from apps.tradings.scheduler import run_trading_workflow

        scheduler = BackgroundScheduler()

        # Schedule the trading workflow to run every custom minutes
        minutes = 5
        scheduler.add_job(
            run_trading_workflow,
            "interval",
            minutes=minutes,
            id="trading_futures_workflow",
            name="Trading Futures Workflow",
            replace_existing=True,
        )

        scheduler.start()
        logger.info(f"✅ APScheduler started - Trading workflow will run every {minutes} minutes")

        # Shutdown scheduler when Django exits
        import atexit

        atexit.register(lambda: scheduler.shutdown())
