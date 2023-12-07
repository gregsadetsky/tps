# Generated by Django 4.2.6 on 2023-12-07 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_round_status_round_winner"),
    ]

    operations = [
        migrations.CreateModel(
            name="TranscriptionLogs",
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
                ("transcript", models.TextField()),
            ],
        ),
    ]
