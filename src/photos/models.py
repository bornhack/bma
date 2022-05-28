from pathlib import Path

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from taggit.managers import TaggableManager

from utils.models import MediaBaseModel
from utils.models import UUIDTaggedItem


def get_photo_upload_path(instance, filename):
    """Return the upload path for this photo."""
    return Path(
        f"photos/user_{instance.gallery.owner.id}/gallery_{instance.gallery.uuid}/photo_{instance.uuid}.{Path(filename).suffix.lower()}",
    )


class Photo(MediaBaseModel):
    """The Photo model."""

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename.",
    )

    photo = models.ImageField(upload_to=get_photo_upload_path)

    small_thumbnail = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(100, 100)],
        format="PNG",
    )

    medium_thumbnail = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(200, 200)],
        format="PNG",
    )

    large_thumbnail = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(300, 300)],
        format="PNG",
    )

    small = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(700, 700)],
        format="PNG",
    )

    medium = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(1000, 1000)],
        format="PNG",
    )

    large = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(1500, 1500)],
        format="PNG",
    )

    slideshow = ImageSpecField(
        source="photo",
        processors=[ResizeToFill(2400, 1600)],
        format="PNG",
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this photo",
    )
