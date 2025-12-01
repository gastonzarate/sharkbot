"""Trading Urls"""

from rest_framework.routers import DefaultRouter
from tradings.views import TradingOperationViewSet, TradingWorkflowExecutionViewSet

router = DefaultRouter()
router.register(r"executions", TradingWorkflowExecutionViewSet, basename="trading-execution")
router.register(r"operations", TradingOperationViewSet, basename="trading-operation")

urlpatterns = router.urls
