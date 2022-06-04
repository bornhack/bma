# Generated by Django 3.2.12 on 2022-06-03 20:07

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import videos.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('galleries', '0003_gallery_tags'),
        ('utils', '0001_initial'),
        ('taggit', '0005_auto_20220424_2025'),
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('galleryfile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='galleries.galleryfile')),
                ('original', models.FileField(help_text='The original uploaded file.', upload_to=videos.models.get_video_upload_path)),
                ('gallery', models.ForeignKey(help_text='The gallery this video belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='galleries.gallery')),
                ('tags', taggit.managers.TaggableManager(help_text='The tags for this video file', through='utils.UUIDTaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
            },
            bases=('galleries.galleryfile',),
        ),
    ]