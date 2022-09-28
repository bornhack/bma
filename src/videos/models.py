from django.db import models
from taggit.managers import TaggableManager

from files.models import BaseFile
from utils.models import UUIDTaggedItem
from utils.upload import get_upload_path


class Video(BaseFile):
    """The Video model."""

    original = models.FileField(
        upload_to=get_upload_path,
        max_length=255,
        help_text="The original uploaded video file.",
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this video file",
    )
