"""This file contains the main BMA model BaseFile and related classes."""
import contextlib
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm
from polymorphic.managers import PolymorphicQuerySet
from polymorphic.models import PolymorphicManager
from polymorphic.models import PolymorphicModel
from users.sentinel import get_sentinel_user

from .validators import validate_file_status
from .validators import validate_thumbnail_url

logger = logging.getLogger("bma")

User = get_user_model()


class StatusChoices(models.TextChoices):
    """The possible status choices for a file."""

    PENDING_MODERATION = ("PENDING_MODERATION", "Pending Moderation")
    UNPUBLISHED = ("UNPUBLISHED", "Unpublished")
    PUBLISHED = ("PUBLISHED", "Published")
    PENDING_DELETION = ("PENDING_DELETION", "Pending Deletion")


license_urls = {
    "CC_ZERO_1_0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC_BY_4_0": "https://creativecommons.org/licenses/by/4.0/",
    "CC_BY_SA_4_0": "https://creativecommons.org/licenses/by-sa/4.0/",
}


class LicenseChoices(models.TextChoices):
    """The choices for license for uploaded files."""

    CC_ZERO_1_0 = ("CC_ZERO_1_0", "Creative Commons CC0 1.0 Universal")
    CC_BY_4_0 = ("CC_BY_4_0", "Creative Commons Attribution 4.0 International")
    CC_BY_SA_4_0 = (
        "CC_BY_SA_4_0",
        "Creative Commons Attribution-ShareAlike 4.0 International",
    )


class FileTypeChoices(models.TextChoices):
    """The filetype filter."""

    picture = ("picture", "Picture")
    video = ("video", "Video")
    audio = ("audio", "Audio")
    document = ("document", "Document")


class BaseFileQuerySet(PolymorphicQuerySet):
    """Custom queryset and manager for file operations."""

    def approve(self) -> int:
        """Approve files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.approve()
        return updated

    def unapprove(self) -> int:
        """Unapprove files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.unapprove()
        return updated

    def publish(self) -> int:
        """Publish files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.publish()
        return updated

    def unpublish(self) -> int:
        """Unpublish files in queryset."""
        updated = 0
        for basefile in self:
            updated += basefile.unpublish()
        return updated


class BaseFile(PolymorphicModel):
    """The polymorphic base model inherited by the Picture, Video, Audio, and Document models."""

    class Meta:
        """Define custom permissions for the BaseFile and inherited models."""

        ordering = ("created",)
        permissions = (
            ("unapprove_basefile", "Unapprove file"),
            ("approve_basefile", "Approve file"),
            ("unpublish_basefile", "Unpublish file"),
            ("publish_basefile", "Publish file"),
        )
        verbose_name = "file"
        verbose_name_plural = "files"

    objects = PolymorphicManager.from_queryset(BaseFileQuerySet)()

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET(get_sentinel_user),
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

    original_source = models.URLField(
        help_text="The URL to the original source of this work. "
        "Leave blank to consider the BMA URL the original source.",
        blank=True,
    )

    license = models.CharField(
        max_length=255,
        choices=LicenseChoices.choices,
        blank=False,
        help_text="The license for this file. The license can not be changed after the file(s) is uploaded.",
    )

    attribution = models.CharField(
        max_length=255,
        help_text="The attribution text for this file. "
        "This is usually the real name or handle of the author(s) or licensor of the file.",
    )

    status = models.CharField(
        max_length=20,
        blank=False,
        validators=[validate_file_status],
        choices=StatusChoices.choices,
        default="PENDING_MODERATION",
        help_text="The status of this file. Only published files are visible on the public website.",
    )

    original_filename = models.CharField(
        max_length=255,
        help_text="The original (uploaded) filename. This value is read-only.",
    )

    file_size = models.PositiveIntegerField(
        help_text="The size of the file in bytes. This value is read-only.",
    )

    thumbnail_url = models.CharField(
        max_length=255,
        validators=[validate_thumbnail_url],
        help_text="Relative URL to the image to use as thumbnail for this file. "
        "This must be a string beginning with /static/images/ or /media/",
    )

    @property
    def filetype(self) -> str:
        """The filetype."""
        return str(self._meta.model_name)

    @property
    def filetype_icon(self) -> str:
        """The filetype icon."""
        return settings.FILETYPE_ICONS[self.filetype]

    @property
    def status_icon(self) -> str:
        """Status icon."""
        return settings.FILESTATUS_ICONS[self.status]

    @property
    def license_name(self) -> str:
        """Get license_name."""
        return str(getattr(LicenseChoices, self.license).label)

    @property
    def license_url(self) -> str:
        """Get license_url."""
        return license_urls[self.license]

    @property
    def source(self) -> str:
        """Consider the BMA canonical URL the source if no other source has been specified."""
        return self.original_source if self.original_source else self.get_absolute_url()

    def get_absolute_url(self) -> str:
        """The detail url for the file."""
        return reverse("files:detail", kwargs={"pk": self.pk})

    def resolve_links(self, request: HttpRequest | None = None) -> dict[str, str | dict[str, str]]:
        """Return a dict of links for various actions on this object.

        Only return the actions the current user has permission to do.
        """
        links: dict[str, str | dict[str, str]] = {
            "self": reverse("api-v1-json:file_get", kwargs={"file_uuid": self.uuid}),
            "html": self.get_absolute_url(),
        }
        downloads: dict[str, str] = {
            "original": self.original.url,
        }
        if request:
            if request.user.has_perm("approve_basefile", self):
                links["approve"] = reverse(
                    "api-v1-json:approve_file",
                    kwargs={"file_uuid": self.uuid},
                )
            if request.user.has_perm("unapprove_basefile", self):
                links["unapprove"] = reverse(
                    "api-v1-json:unapprove_file",
                    kwargs={"file_uuid": self.uuid},
                )
            if request.user.has_perm("publish_basefile", self):
                links["publish"] = reverse(
                    "api-v1-json:publish_file",
                    kwargs={"file_uuid": self.uuid},
                )
            if request.user.has_perm("unpublish_basefile", self):
                links["unpublish"] = reverse(
                    "api-v1-json:unpublish_file",
                    kwargs={"file_uuid": self.uuid},
                )
        if self.filetype == "picture":
            # maybe file is missing from disk so suppress OSError
            with contextlib.suppress(OSError):
                downloads.update(
                    {
                        "small_thumbnail": self.small_thumbnail.url,
                        "medium_thumbnail": self.medium_thumbnail.url,
                        "large_thumbnail": self.large_thumbnail.url,
                        "small": self.small.url,
                        "medium": self.medium.url,
                        "large": self.large.url,
                        "slideshow": self.slideshow.url,
                    }
                )
        links["downloads"] = downloads
        return links

    def update_status(self, new_status: str) -> int:
        """Update the status of a file."""
        self.status = new_status
        try:
            self.full_clean()
            self.save(update_fields=["status", "updated"])
        except ValidationError:
            logger.exception("Invalid file status.")
            return 0
        return 1

    def approve(self) -> int:
        """Approve this file and add publish/unpublish permissions to the uploader."""
        assign_perm("publish_basefile", self.uploader, self)
        assign_perm("unpublish_basefile", self.uploader, self)
        return self.unpublish()

    def unapprove(self) -> int:
        """Unapprove this file and remove publish/unpublish permissions from the uploader."""
        remove_perm("publish_basefile", self.uploader, self)
        remove_perm("unpublish_basefile", self.uploader, self)
        return self.update_status(new_status="PENDING_MODERATION")

    def publish(self) -> int:
        """Publish this file."""
        return self.update_status(new_status="PUBLISHED")

    def unpublish(self) -> int:
        """Unpublish this file."""
        return self.update_status(new_status="UNPUBLISHED")

    def add_initial_permissions(self) -> None:
        """Add initial permissions for newly uploaded files."""
        # add uploader permissions
        assign_perm("view_basefile", self.uploader, self)
        assign_perm("change_basefile", self.uploader, self)
        assign_perm("delete_basefile", self.uploader, self)
        moderators, created = Group.objects.get_or_create(name=settings.BMA_MODERATOR_GROUP_NAME)
        if created:
            logger.debug("Created new group 'moderators'")
        # add moderator permissions
        assign_perm("view_basefile", moderators, self)
        assign_perm("approve_basefile", moderators, self)
        assign_perm("unapprove_basefile", moderators, self)
