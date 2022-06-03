from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from taggit.managers import TaggableManager

from utils.models import BaseModel
from utils.models import UUIDTaggedItem


class StatusChoices(models.TextChoices):
    PENDING = ("PENDING", "Pending Moderation")
    PUBLISHED = ("PUBLISHED", "Published")
    UNPUBLISHED = ("UNPUBLISHED", "Unpublished")
    DELETED = ("DELETED", "Deleted")


class Gallery(BaseModel):
    """The Gallery class is used for grouping uploaded files."""

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="galleries",
        help_text="The creator and copyright holder for this gallery.",
    )

    name = models.CharField(
        max_length=100,
        help_text="The name of this gallery. Keep it under 100 characters please.",
    )

    description = models.TextField(
        blank=True,
        help_text="The description of this gallery. Optional.",
    )

    slug = models.SlugField(
        blank=True,
        help_text="The URL slug for this gallery. Leave blank to generate based on name.",
    )

    tags = TaggableManager(through=UUIDTaggedItem)

    license = models.CharField(
        max_length=20,
        choices=settings.LICENSES,
        help_text="The license for files in this gallery.",
    )

    attribution = models.CharField(
        max_length=255,
        help_text="The attribution text for files in this gallery. This is usually the real name of the creator/copyright holder.",
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default="PENDING",
        help_text="The status of this gallery. Only published galleries are visible on the website.",
    )

    def get_absolute_url(self):
        return reverse("galleries:gallery_detail", kwargs={"slug": self.slug})


class GalleryFile(BaseModel):
    """The base model inherited by the Photo, Video, Audio, and Document models."""

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        help_text="The status of this file. Only published files are visible on the website.",
    )

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename.",
    )

    @property
    def file(self):
        if self.photo:
            return self.photo
        elif self.video:
            return self.video
        elif self.audio:
            return self.audio
        elif self.document:
            return self.document
        else:
            return False

    @property
    def filetype(self):
        if self.photo:
            return "photo"
        elif self.video:
            return "video"
        elif self.audio:
            return "audio"
        elif self.document:
            return "document"
        else:
            return False
