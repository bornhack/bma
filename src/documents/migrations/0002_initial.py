# Generated by Django 4.1.2 on 2022-10-16 15:18

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("utils", "0001_initial"),
        ("documents", "0001_initial"),
        ("taggit", "0005_auto_20220424_2025"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="tags",
            field=taggit.managers.TaggableManager(
                help_text="The tags for this document file",
                through="utils.UUIDTaggedItem",
                to="taggit.Tag",
                verbose_name="Tags",
            ),
        ),
    ]
