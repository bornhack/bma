import uuid

from django.db import models
from taggit.models import GenericUUIDTaggedItemBase
from taggit.models import TaggedItemBase


class BaseModel(models.Model):
    """The BaseModel which all other models are based on."""

    class Meta:
        abstract = True

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    """Allows us to tag models with a UUID pk, use it with TaggableManager(through=UUIDTaggedItem)"""

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class MediaBaseModel(BaseModel):
    """The base model shared by the Photo, Video, Audio, and Document models."""

    class Meta:
        abstract = True

    gallery = models.ForeignKey(
        "galleries.Gallery",
        on_delete=models.CASCADE,
        related_name="gallery_%(class)ss",
        help_text="The gallery this file belongs to.",
    )

    class StatusChoices(models.TextChoices):
        PENDING = ("PENDING", "Pending Moderation")
        PUBLISHED = ("PUBLISHED", "Published")
        UNPUBLISHED = ("UNPUBLISHED", "Unpublished")
        DELETED = ("DELETED", "Deleted")

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        help_text="The status of this file. Only published files are visible on the website.",
    )
