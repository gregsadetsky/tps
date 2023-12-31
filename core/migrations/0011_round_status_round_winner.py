# Generated by Django 4.2.6 on 2023-12-07 20:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_round_remove_caller_game_alter_caller_state_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="round",
            name="status",
            field=models.CharField(
                choices=[("unknown", "unknown"), ("tie", "tie"), ("won", "won")],
                default="unknown",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="round",
            name="winner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.caller",
            ),
        ),
    ]
