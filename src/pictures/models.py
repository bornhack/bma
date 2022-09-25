from pathlib import Path

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from taggit.managers import TaggableManager

from galleries.models import GalleryFile
from utils.models import UUIDTaggedItem


def get_picture_upload_path(instance, filename):
    """Return the upload path under MEDIA_ROOT for this picture."""
    return Path(
        f"pictures/user_{instance.gallery.owner.id}/gallery_{instance.gallery.uuid}/picture_{instance.uuid}{Path(filename).suffix.lower()}",
    )


class Picture(GalleryFile):
    """The Picture model."""

    original = models.ImageField(
        upload_to=get_picture_upload_path,
        max_length=255,
        help_text="The original uploaded picture file.",
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
