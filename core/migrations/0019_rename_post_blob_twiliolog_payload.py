# Generated by Django 4.2.6 on 2023-12-08 19:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_twiliolog_view_function"),
    ]

    operations = [
        migrations.RenameField(
            model_name="twiliolog",
            old_name="post_blob",
            new_name="payload",
        ),
    ]