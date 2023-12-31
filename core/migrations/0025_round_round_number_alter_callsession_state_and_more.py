# Generated by Django 4.2.6 on 2023-12-14 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_callerperson_callsession_caller_person"),
    ]

    operations = [
        migrations.AddField(
            model_name="round",
            name="round_number",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="callsession",
            name="state",
            field=models.CharField(
                choices=[
                    ("hungup", "hungup"),
                    ("being_welcomed", "being_welcomed"),
                    ("waiting_for_other_player", "waiting_for_other_player"),
                    ("started_game", "started_game"),
                    ("rerecording", "rerecording"),
                    ("waiting_for_transcript", "waiting_for_transcript"),
                    ("listening_to_results", "listening_to_results"),
                ],
                max_length=255,
            ),
        ),
        migrations.AddConstraint(
            model_name="round",
            constraint=models.UniqueConstraint(
                fields=("player1_session", "player2_session", "round_number"),
                name="unique_rounds",
            ),
        ),
    ]
