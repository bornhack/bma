import uuid

from django.db import models
from polymorphic.models import PolymorphicModel

from utils.license import LicenseChoices


class StatusChoices(models.TextChoices):
    """The possible status choices for a file."""

    PENDING_MODERATION = ("PENDING_MODERATION", "Pending Moderation")
    UNPUBLISHED = ("UNPUBLISHED", "Unpublished")
    PUBLISHED = ("PUBLISHED", "Published")
    PENDING_DELETION = ("PENDING_DELETION", "Pending Deletion")


class BaseFile(PolymorphicModel):
    """The polymorphic base model inherited by the Picture, Video, Audio, and Document models."""

    class Meta:
        ordering = ["created"]

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="files",
        help_text="The uploader of this file.",
    )

    created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this object was first created.",
    )

    updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this object was last updated.",
    )

    title = models.CharField(
        max_length=255,
        blank=False,
        help_text="The title of this work. Required. Defaults to the original uploaded filename.",
    )

    description = models.TextField(
        blank=True,
        help_text="The description of this work. Optional. Supports markdown.",
    )

    source = models.URLField(
        help_text="The URL to the original source of this work. Leave blank to consider the BMA URL the original source.",
    )

    license = models.CharField(
        max_length=255,
        choices=LicenseChoices.choices,
        blank=False,
        help_text="The license for this file.",
    )

    attribution = models.CharField(
        max_length=255,
        help_text="The attribution text for this file. This is usually the real name or handle of the author(s) or licensor of the file.",
    )

    status = models.CharField(
        max_length=20,
        blank=False,
        choices=StatusChoices.choices,
        default="PENDING_MODERATION",
        help_text="The status of this file. Only published files are visible on the public website.",
    )

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename.",
    )

    @property
    def filetype(self):
        return self._meta.model_name
