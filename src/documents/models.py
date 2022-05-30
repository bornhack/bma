from pathlib import Path

from django.db import models
from taggit.managers import TaggableManager

from utils.models import MediaBaseModel
from utils.models import UUIDTaggedItem


def get_document_upload_path(instance, filename):
    """Return the upload path for this document file."""
    return Path(
        f"documents/user_{instance.gallery.owner.id}/gallery_{instance.gallery.uuid}/document_{instance.uuid}.{Path(filename).suffix.lower()}",
    )


class Document(MediaBaseModel):
    """The Document model."""

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename.",
    )

    document = models.FileField(upload_to=get_document_upload_path)

    tags = TaggableManager(
        through=UUIDTaggedItem,
        help_text="The tags for this document file",
    )
