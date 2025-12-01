# Generated manually for temporal context implementation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tradings", "0002_tradingworkflowexecution_agent_streaming_output_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tradingworkflowexecution",
            name="execution_frequency_minutes",
            field=models.IntegerField(default=15, help_text="Frequency of workflow execution in minutes"),
        ),
        migrations.AddField(
            model_name="tradingworkflowexecution",
            name="strategy_for_next_execution",
            field=models.TextField(
                blank=True,
                help_text="Agent's strategic plan and context for the next execution (agent memory)",
            ),
        ),
    ]
