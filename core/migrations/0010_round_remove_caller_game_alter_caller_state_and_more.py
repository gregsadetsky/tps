# Generated by Django 4.2.6 on 2023-12-07 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_game_last_player_1_move_game_last_player_2_move"),
    ]

    operations = [
        migrations.CreateModel(
            name="Round",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "last_player_1_move",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "last_player_2_move",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="caller",
            name="game",
        ),
        migrations.AlterField(
            model_name="caller",
            name="state",
            field=models.CharField(
                choices=[
                    ("hungup", "hungup"),
                    ("waiting_for_other_player", "waiting_for_other_player"),
                    ("started_game", "started_game"),
                    ("waiting_for_transcript", "waiting_for_transcript"),
                ],
                max_length=255,
            ),
        ),
        migrations.DeleteModel(
            name="Game",
        ),
        migrations.AddField(
            model_name="round",
            name="player1",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="player1",
                to="core.caller",
            ),
        ),
        migrations.AddField(
            model_name="round",
            name="player2",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="player2",
                to="core.caller",
            ),
        ),
    ]
