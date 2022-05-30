from pathlib import Path

from django.db import models
from taggit.managers import TaggableManager

from utils.models import MediaBaseModel
from utils.models import UUIDTaggedItem


def get_video_upload_path(instance, filename):
    """Return the upload path for this video file."""
    return Path(
        f"videos/user_{instance.gallery.owner.id}/gallery_{instance.gallery.uuid}/video_{instance.uuid}.{Path(filename).suffix.lower()}",
    )


class Video(MediaBaseModel):
    """The Video model."""

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename.",
    )

    video = models.FileField(upload_to=get_video_upload_path)

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this video file",
    )
