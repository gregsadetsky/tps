# Generated by Django 4.2.6 on 2023-12-08 19:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_round_player1_recording_url_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="round",
            old_name="last_player_1_move",
            new_name="player_1_move",
        ),
        migrations.RenameField(
            model_name="round",
            old_name="last_player_2_move",
            new_name="player_2_move",
        ),
    ]
