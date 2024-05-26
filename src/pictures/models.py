"""The Picture model."""
from django.db import models
from files.models import BaseFile
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from taggit.managers import TaggableManager
from utils.models import UUIDTaggedItem
from utils.upload import get_upload_path


class Picture(BaseFile):  # type: ignore[django-manager-missing]
    """The Picture model."""

    original = models.ImageField(
        upload_to=get_upload_path,
        max_length=255,
        help_text="The original uploaded picture.",
    )

    small_thumbnail = ImageSpecField(
        source="original",
        processors=[ResizeToFit(150, 150)],
        format="JPEG",
        options={"quality": 60},
    )

    large_thumbnail = ImageSpecField(
        source="original",
        processors=[ResizeToFit(300, 300)],
        format="JPEG",
        options={"quality": 60},
    )

    small = ImageSpecField(
        source="original",
        processors=[ResizeToFit(600, 600)],
        format="JPEG",
        options={"quality": 60},
    )

    medium = ImageSpecField(
        source="original",
        processors=[ResizeToFit(1200, 1200)],
        format="JPEG",
        options={"quality": 60},
    )

    large = ImageSpecField(
        source="original",
        processors=[ResizeToFit(2400, 2400)],
        format="JPEG",
        options={"quality": 60},
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this picture",
    )
