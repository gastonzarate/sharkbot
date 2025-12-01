import json

from django.contrib import admin
from django.utils.html import format_html

from tradings.models import TradingOperation, TradingWorkflowExecution


@admin.register(TradingOperation)
class TradingOperationAdmin(admin.ModelAdmin):
    list_display = [
        "operation_type",
        "currency",
        "quantity",
        "leverage",
        "status",
        "created_at",
    ]
    list_filter = ["operation_type", "status", "created_at", "currency"]
    search_fields = ["currency", "main_order_id", "error_message"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "result_data",
        "main_order_id",
        "stop_loss_order_id",
        "take_profit_order_id",
    ]
    ordering = ["-created_at"]


@admin.register(TradingWorkflowExecution)
class TradingWorkflowExecutionAdmin(admin.ModelAdmin):
    """Admin interface for Trading Workflow Executions."""

    list_display = [
        "created_at",
        "status_badge",
        "currencies_display",
        "balance_display",
        "pnl_display",
        "duration_display",
        "positions_count",
    ]

    list_filter = [
        "status",
        "created_at",
    ]

    search_fields = [
        "agent_response",
        "error_message",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "status",
        "execution_duration",
        "currencies",
        "balance_info_formatted",
        "market_data_formatted",
        "open_positions_formatted",
        "daily_pnl_formatted",
        "agent_response",
        "error_message",
        "error_traceback",
    ]

    fieldsets = (
        (
            "Execution Info",
            {"fields": ("id", "created_at", "updated_at", "status", "execution_duration", "currencies")},
        ),
        (
            "Balance",
            {
                "fields": ("balance_info_formatted",),
            },
        ),
        (
            "Market Data",
            {
                "fields": ("market_data_formatted",),
                "classes": ("collapse",),
            },
        ),
        (
            "Positions",
            {
                "fields": ("open_positions_formatted",),
            },
        ),
        (
            "Performance",
            {
                "fields": ("daily_pnl_formatted",),
            },
        ),
        (
            "Agent Response",
            {
                "fields": ("agent_response",),
            },
        ),
        (
            "Errors",
            {
                "fields": ("error_message", "error_traceback"),
                "classes": ("collapse",),
            },
        ),
    )

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            "SUCCESS": "green",
            "ERROR": "red",
            "TIMEOUT": "orange",
            "RUNNING": "blue",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status,
        )

    status_badge.short_description = "Status"

    def currencies_display(self, obj):
        """Display currencies as comma-separated list."""
        return ", ".join(obj.currencies) if obj.currencies else "N/A"

    currencies_display.short_description = "Currencies"

    def balance_display(self, obj):
        """Display total balance."""
        balance = obj.balance_info.get("total_wallet_balance", 0)
        return f"${balance:.2f}"

    balance_display.short_description = "Balance"

    def pnl_display(self, obj):
        """Display daily PnL with color."""
        pnl = obj.daily_pnl.get("daily_realized_pnl", 0)
        color = "green" if pnl >= 0 else "red"
        return format_html('<span style="color: {};">{}</span>', color, f"${pnl:.2f}")

    pnl_display.short_description = "Daily PnL"

    def duration_display(self, obj):
        """Display execution duration."""
        if obj.execution_duration:
            return f"{obj.execution_duration:.2f}s"
        return "N/A"

    duration_display.short_description = "Duration"

    def positions_count(self, obj):
        """Display number of open positions."""
        return len(obj.open_positions)

    positions_count.short_description = "Positions"

    def balance_info_formatted(self, obj):
        """Format balance info as readable JSON."""
        return format_html("<pre>{}</pre>", json.dumps(obj.balance_info, indent=2))

    balance_info_formatted.short_description = "Balance Info"

    def market_data_formatted(self, obj):
        """Format market data as readable JSON."""
        return format_html("<pre>{}</pre>", json.dumps(obj.market_data, indent=2))

    market_data_formatted.short_description = "Market Data"

    def open_positions_formatted(self, obj):
        """Format positions as readable JSON."""
        return format_html("<pre>{}</pre>", json.dumps(obj.open_positions, indent=2))

    open_positions_formatted.short_description = "Open Positions"

    def daily_pnl_formatted(self, obj):
        """Format daily PnL as readable JSON."""
        return format_html("<pre>{}</pre>", json.dumps(obj.daily_pnl, indent=2))

    daily_pnl_formatted.short_description = "Daily Performance"
