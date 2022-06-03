from pathlib import Path

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit
from taggit.managers import TaggableManager

from galleries.models import GalleryFile
from utils.models import UUIDTaggedItem


def get_photo_upload_path(instance, filename):
    """Return the upload path under MEDIA_ROOT for this photo."""
    # with open(instance.photo) as f:
    #    mime = magic.from_buffer(f.read(), mime=True)
    #    print(mime)
    return Path(
        f"photos/user_{instance.gallery.owner.id}/gallery_{instance.gallery.uuid}/photo_{instance.uuid}.{Path(filename).suffix.lower()}",
    )


class Photo(GalleryFile):
    """The Photo model."""

    gallery = models.ForeignKey(
        "galleries.Gallery",
        on_delete=models.CASCADE,
        related_name="photos",
        help_text="The gallery this photo belongs to.",
    )

    original = models.ImageField(
        upload_to=get_photo_upload_path,
        help_text="The original uploaded file.",
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
        help_text="The tags for this photo",
    )
