# Generated by Django 4.2.6 on 2023-12-14 02:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_alter_callsession_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="threadsafe",
            name="key",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
