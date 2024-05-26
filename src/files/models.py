"""This file contains the main BMA model BaseFile and related classes."""
import contextlib
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import assign_perm
from guardian.shortcuts import get_objects_for_user
from polymorphic.managers import PolymorphicQuerySet
from polymorphic.models import PolymorphicManager
from polymorphic.models import PolymorphicModel
from users.sentinel import get_sentinel_user

from .validators import validate_thumbnail_url

logger = logging.getLogger("bma")

User = get_user_model()


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

    def change_bool(self, *, field: str, value: bool) -> int:
        """Change a bool field on a queryset of files."""
        kwargs = {field: value, "updated": timezone.now()}
        self.update(**kwargs)
        return int(self.count())

    def approve(self) -> int:
        """Approve files in queryset."""
        return self.change_bool(field="approved", value=True)

    def unapprove(self) -> int:
        """Unapprove files in queryset."""
        return self.change_bool(field="approved", value=False)

    def publish(self) -> int:
        """Publish files in queryset."""
        return self.change_bool(field="published", value=True)

    def unpublish(self) -> int:
        """Unpublish files in queryset."""
        return self.change_bool(field="published", value=False)

    def delete(self) -> int:
        """Delete files in queryset."""
        return self.change_bool(field="deleted", value=True)

    def undelete(self) -> int:
        """Undelete files in queryset."""
        return self.change_bool(field="deleted", value=False)

    def get_permitted(self, user: User) -> models.QuerySet["BaseFile"]:  # type: ignore[valid-type]
        """Return files that are approved, published and not deleted, plus files where the user has view_basefile."""
        approved_files = self.filter(approved=True, published=True, deleted=False).prefetch_related("uploader")
        perm_files = get_objects_for_user(
            user=user,
            perms="files.view_basefile",
            klass=self.all(),
        ).prefetch_related("uploader")
        files = approved_files | perm_files
        # do not return duplicates
        return files.distinct()  # type: ignore[no-any-return]


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
            ("undelete_basefile", "Undelete file"),
            ("softdelete_basefile", "Soft delete file"),
        )
        verbose_name = "file"
        verbose_name_plural = "files"

    objects = PolymorphicManager()

    bmanager = PolymorphicManager.from_queryset(BaseFileQuerySet)()

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

    approved = models.BooleanField(
        default=False,
        help_text="Has this file been approved by a moderator?",
    )

    published = models.BooleanField(
        default=False,
        help_text="Has this file been published?",
    )

    deleted = models.BooleanField(
        default=False,
        help_text="Has this file been deleted?",
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
                        "large_thumbnail": self.large_thumbnail.url,
                        "small": self.small.url,
                        "medium": self.medium.url,
                        "large": self.large.url,
                    }
                )
        links["downloads"] = downloads
        return links

    def update_field(self, *, field: str, value: bool) -> None:
        """Update a bool field on the model atomically."""
        setattr(self, field, value)
        self.save(update_fields=[field, "updated"])

    def approve(self) -> None:
        """Approve this file and add publish/unpublish permissions to the uploader."""
        self.update_field(field="approved", value=True)

    def unapprove(self) -> None:
        """Unapprove this file and remove publish/unpublish permissions from the uploader."""
        self.update_field(field="approved", value=False)

    def publish(self) -> None:
        """Publish this file."""
        self.update_field(field="published", value=True)

    def unpublish(self) -> None:
        """Unpublish this file."""
        self.update_field(field="published", value=False)

    def softdelete(self) -> None:
        """Soft delete this file."""
        self.update_field(field="deleted", value=True)

    def undelete(self) -> None:
        """Undelete this file."""
        self.update_field(field="deleted", value=False)

    def add_initial_permissions(self) -> None:
        """Add initial permissions for newly uploaded files."""
        # add uploader permissions
        assign_perm("view_basefile", self.uploader, self)
        assign_perm("change_basefile", self.uploader, self)
        assign_perm("publish_basefile", self.uploader, self)
        assign_perm("unpublish_basefile", self.uploader, self)
        assign_perm("softdelete_basefile", self.uploader, self)
        assign_perm("undelete_basefile", self.uploader, self)
        moderators, created = Group.objects.get_or_create(name=settings.BMA_MODERATOR_GROUP_NAME)
        if created:
            logger.debug("Created new group 'moderators'")
        # add moderator permissions
        assign_perm("view_basefile", moderators, self)
        assign_perm("approve_basefile", moderators, self)
        assign_perm("unapprove_basefile", moderators, self)

    def permitted(self, user: User) -> bool:  # type: ignore[valid-type]
        """Convenience method to determine if viewing this file is permitted for a user."""
        if user.has_perm("files.view_basefile", self) or all([self.approved, self.published, not self.deleted]):  # type: ignore[attr-defined]
            return True
        return False
