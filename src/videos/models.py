"""The Video model."""

from django.db import models

from files.models import BaseFile
from utils.upload import get_upload_path


class Video(BaseFile):
    """The Video model."""

    original = models.FileField(
        upload_to=get_upload_path,
        max_length=255,
        help_text="The original uploaded video file.",
    )
