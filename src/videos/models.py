from pathlib import Path

from django.db import models
from taggit.managers import TaggableManager

from galleries.models import GalleryFile
from utils.models import UUIDTaggedItem


def get_video_upload_path(instance, filename):
    """Return the upload path for this video file."""
    return Path(
        f"videos/user_{instance.gallery.owner.id}/gallery_{instance.gallery.uuid}/video_{instance.uuid}{Path(filename).suffix.lower()}",
    )


class Video(GalleryFile):
    """The Video model."""

    original = models.FileField(
        upload_to=get_video_upload_path,
        help_text="The original uploaded video file.",
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this video file",
    )
