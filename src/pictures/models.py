from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from taggit.managers import TaggableManager

from files.models import BaseFile
from utils.models import UUIDTaggedItem
from utils.upload import get_upload_path


class Picture(BaseFile):
    """The Picture model."""

    original = models.ImageField(
        upload_to=get_upload_path,
        max_length=255,
        help_text="The original uploaded picture.",
    )

    small_thumbnail = ImageSpecField(
        source="original",
        processors=[ResizeToFit(100, 100)],
        format="JPEG",
    )

    medium_thumbnail = ImageSpecField(
        source="original",
        processors=[ResizeToFit(200, 200)],
        format="JPEG",
    )

    large_thumbnail = ImageSpecField(
        source="original",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
    )

    small = ImageSpecField(
        source="original",
        processors=[ResizeToFit(700, 700)],
        format="JPEG",
    )

    medium = ImageSpecField(
        source="original",
        processors=[ResizeToFit(1000, 1000)],
        format="JPEG",
    )

    large = ImageSpecField(
        source="original",
        processors=[ResizeToFit(1500, 1500)],
        format="JPEG",
    )

    slideshow = ImageSpecField(
        source="original",
        processors=[ResizeToFit(2400, 1600)],
        format="JPEG",
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this picture",
    )
