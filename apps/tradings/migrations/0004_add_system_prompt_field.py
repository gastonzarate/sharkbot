# Generated manually for system_prompt field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tradings", "0003_add_temporal_context_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="tradingworkflowexecution",
            name="system_prompt",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Complete system prompt provided to the agent with all context",
            ),
        ),
    ]
