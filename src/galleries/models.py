import uuid

from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from polymorphic.models import PolymorphicModel
from taggit.managers import TaggableManager

from utils.models import BaseModel
from utils.models import UUIDTaggedItem


class StatusChoices(models.TextChoices):
    PENDING_MODERATION = ("PENDING_MODERATION", "Pending Moderation")
    UNPUBLISHED = ("UNPUBLISHED", "Unpublished")
    PUBLISHED = ("PUBLISHED", "Published")
    PENDING_DELETION = ("PENDING_DELETION", "Pending Deletion")


class Gallery(BaseModel):
    """The Gallery class is used for grouping uploaded files."""

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="galleries",
        help_text="The uploader of this gallery.",
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
        default="PENDING_MODERATION",
        help_text="The status of this gallery. Only published galleries are visible on the website.",
    )

    def get_absolute_url(self):
        return reverse("galleries:gallery_manage_detail", kwargs={"slug": self.slug})

    @property
    def pictures(self):
        from pictures.models import Picture

        return self.galleryfiles.instance_of(Picture)

    @property
    def videos(self):
        from videos.models import Video

        return self.galleryfiles.instance_of(Video)

    @property
    def audios(self):
        from audios.models import Audio

        return self.galleryfiles.instance_of(Audio)

    @property
    def documents(self):
        from documents.models import Document

        return self.galleryfiles.instance_of(Document)


class GalleryFile(PolymorphicModel):
    """The polymorphic base model inherited by the Picture, Video, Audio, and Document models."""

    class Meta:
        ordering = ["created"]

    gallery = models.ForeignKey(
        "galleries.Gallery",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        help_text="The gallery this file belongs to.",
    )

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
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
        help_text="The description of this file. Optional.",
    )

    source = models.URLField(
        help_text="The URL to the original source of this work. Leave blank to consider the BMA URL the original source.",
    )

    status = models.CharField(
        max_length=20,
        blank=False,
        choices=StatusChoices.choices,
        default="PENDING_MODERATION",
        help_text="The status of this file. Only published files are visible on the public website (as long as the gallery is also published).",
    )

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename.",
    )

    @property
    def filetype(self):
        return self._meta.model_name
