# Generated by Django 4.1.1 on 2022-09-24 21:17

import audios.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audios", "0002_audio_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audio",
            name="original",
            field=models.FileField(
                help_text="The original uploaded file.",
                max_length=255,
                upload_to=audios.models.get_audio_upload_path,
            ),
        ),
    ]
