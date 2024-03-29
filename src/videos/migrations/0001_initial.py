# Generated by Django 4.1.2 on 2022-10-16 15:18

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import utils.upload


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("files", "0002_initial"),
        ("utils", "0001_initial"),
        ("taggit", "0005_auto_20220424_2025"),
    ]

    operations = [
        migrations.CreateModel(
            name="Video",
            fields=[
                (
                    "basefile_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="files.basefile",
                    ),
                ),
                (
                    "original",
                    models.FileField(
                        help_text="The original uploaded video file.",
                        max_length=255,
                        upload_to=utils.upload.get_upload_path,
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(
                        help_text="The tags for this video file",
                        through="utils.UUIDTaggedItem",
                        to="taggit.Tag",
                        verbose_name="Tags",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("files.basefile",),
        ),
    ]
