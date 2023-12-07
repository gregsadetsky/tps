# Generated by Django 4.2.6 on 2023-12-07 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_transcriptionlogs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caller",
            name="state",
            field=models.CharField(
                choices=[
                    ("hungup", "hungup"),
                    ("waiting_for_other_player", "waiting_for_other_player"),
                    ("started_game", "started_game"),
                    ("rerecording", "rerecording"),
                    ("waiting_for_transcript", "waiting_for_transcript"),
                ],
                max_length=255,
            ),
        ),
    ]
