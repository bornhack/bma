"""This file contains the main BMA model BaseFile and related classes."""

# mypy: disable-error-code="var-annotated"
import logging
import math
import uuid
from fractions import Fraction
from pathlib import Path
from typing import TypeAlias

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from guardian.models import GroupObjectPermissionBase
from guardian.models import UserObjectPermissionBase
from guardian.shortcuts import assign_perm
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel
from taggit.managers import TaggableManager
from taggit.utils import _parse_tags

from jobs.models import ThumbnailJob
from jobs.models import ThumbnailSourceJob
from tags.managers import BMATagManager
from tags.models import TaggedFile
from users.models import UserType
from users.sentinel import get_sentinel_user
from utils.models import BaseModel
from utils.models import NoPillowPictureField
from utils.upload import get_thumbnail_source_path

from .managers import BaseFileManager
from .managers import BaseFileQuerySet

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

    image = ("image", "Image")
    video = ("video", "Video")
    audio = ("audio", "Audio")
    document = ("document", "Document")


class BaseFile(PolymorphicModel):
    """The polymorphic base model inherited by the Image, Video, Audio, and Document models."""

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

    objects = PolymorphicManager.from_queryset(BaseFileQuerySet)()

    bmanager = BaseFileManager.from_queryset(BaseFileQuerySet)()

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

    file_size = models.BigIntegerField(
        help_text="The size of the file in bytes. This value is read-only.",
    )

    mimetype = models.CharField(
        max_length=255,
        help_text="The mimetype of the original (uploaded) file as reported "
        "by the uploading client. This value is read-only.",
    )

    tags = TaggableManager(
        through=TaggedFile,
        manager=BMATagManager,
        help_text="The tags for this file",
    )

    @property
    def filetype(self) -> str:
        """The filetype."""
        return str(self._meta.model_name)

    def __str__(self) -> str:
        """A string representation."""
        return f"{self.title} ({self.filetype} {self.pk})"

    @property
    def filetype_icon(self) -> str:
        """The filetype icon."""
        return settings.FILETYPE_ICONS[self.filetype]

    @property
    def filename(self) -> str:
        """Get the filename."""
        return Path(self.original.path).name

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
        return self.original_source if self.original_source else self.get_absolute_url()  # type: ignore[no-any-return]

    def get_absolute_url(self) -> str:
        """The detail url for the file."""
        return reverse("files:file_detail", kwargs={"file_uuid": self.pk})

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
        if hasattr(self, "thumbnail"):
            downloads["thumbnail_source"] = self.thumbnail.source.url
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
        # add moderator permissions
        moderators = Group.objects.get(name=settings.BMA_MODERATOR_GROUP_NAME)
        assign_perm("view_basefile", moderators, self)
        assign_perm("approve_basefile", moderators, self)
        assign_perm("unapprove_basefile", moderators, self)

    def permitted(self, user: UserType | AnonymousUser) -> bool:
        """Convenience method to determine if viewing this file is permitted for a user."""
        return user.has_perm("files.view_basefile", self) or all([self.approved, self.published])

    @property
    def thumbnail_path(self) -> Path:
        """Return the path for the thumbnails for this file."""
        path = Path(self.original.path)
        return path.parent / path.stem / "thumbnails"

    def parse_and_add_tags(self, tags: str, tagger: UserType) -> None:
        """Parse a string of one or more tags and add tags to the file."""
        self.tags.add_user_tags(*_parse_tags(tags), user=tagger)

    def create_jobs(self) -> None:
        """Default create_jobs for filetypes that have no extra jobs to do."""
        self.create_thumbnail_jobs()

    def create_thumbnail_jobs(self) -> None:
        """Create jobs to make thumbnails."""
        if not hasattr(self, "thumbnail"):
            # no thumbnail to work with yet, but make sure there is a ThumbnailSourceJob
            ThumbnailSourceJob.objects.get_or_create(
                basefile=self,
                path=self.thumbnail_path,
            )
            return
        for version in self.thumbnail.source.get_picture_files_list():
            # check if this file already exists
            if version.path.exists():
                continue
            # file missing, a new job must be created
            _, (_, filetype, ratio, _, width), _ = version.deconstruct()
            if version.height:
                height = version.height
            else:
                height = self.calculate_version_height(width=width, ratio=ratio if ratio else self.aspect_ratio)
            job, created = ThumbnailJob.objects.get_or_create(
                basefile=self,
                path=version.name,
                width=width,
                height=height,
                custom_aspect_ratio=bool(ratio),
                filetype=filetype,
            )

    def get_picturefield_versions(
        self, field: "NoPillowPictureField"
    ) -> dict[str, dict[str, list[tuple[int, int, str]]]]:
        """Return a tuple of width, height, ratio, format for all versions of this file."""
        versions: dict[str, dict[str, list[tuple[int, int, str]]]] = {}
        # get the ratio of the source instance, used to calculate the height
        # for versions with default AR
        source_ratio = Fraction(field.instance.width / field.instance.height)
        for ratio, filetypes in field.aspect_ratios.items():
            # initialise a dict to hold all filetypes for this ratio
            versions[ratio] = {}
            for filetype, sizes in filetypes.items():
                # initialise list to hold all sizes for this filetype
                versions[ratio][filetype] = []
                for width, version in sizes.items():
                    url = version.url if Path(version.path).exists() else ""
                    height = self.calculate_version_height(
                        width=width, ratio=Fraction(ratio) if ratio else source_ratio
                    )
                    versions[ratio][filetype].append((width, height, url))
                versions[ratio][filetype].sort(reverse=True)
        return versions

    def calculate_version_height(self, width: int, ratio: Fraction) -> int:
        """Calculate the height for an image version."""
        if ratio != self.aspect_ratio:
            # custom aspect ratio
            return math.floor(width / ratio)
        # maintain original AR
        return int(math.floor(width / self.aspect_ratio))

    def get_thumbnail_versions(self) -> dict[str, dict[str, list[tuple[int, int, str]]]]:
        """Return thumbnails."""
        if not self.thumbnail:
            return {}
        return self.get_picturefield_versions(field=self.thumbnail.source)


class Thumbnail(BaseModel):
    """Model to contain thumbnails for files.

    Thumbnails of various sizes and ARs are created from the source image.

    If a BaseFile doesn't have a Thumbnail object yet some default thumbnail images
    are used based on the filetype.
    """

    basefile = models.OneToOneField(
        "files.BaseFile",
        on_delete=models.CASCADE,  # delete thumbnail when a basefile is deleted
        help_text="The basefile these thumbnails are for.",
    )

    source = NoPillowPictureField(
        upload_to=get_thumbnail_source_path,
        max_length=255,
        width_field="width",
        height_field="height",
        aspect_ratios=[None, "1/1", "4/3", "16/9"],
        container_width=200,
        grid_columns=4,
        pixel_densities=[1, 2],
        help_text="The source image from which all the thumbnails are created.",
    )

    width = models.PositiveIntegerField(
        help_text="The width of the thumbnail source (in pixels).",
    )

    height = models.PositiveIntegerField(
        help_text="The height of the thumbnail source (in pixels).",
    )

    mimetype = models.CharField(
        max_length=255,
        help_text="The mimetype of the thumbnail source image as reported by the uploading client.",
    )


class FileUserObjectPermission(UserObjectPermissionBase):
    """Use a direct (non-generic) FK for user file permissions in guardian."""

    content_object = models.ForeignKey(BaseFile, related_name="user_permissions", on_delete=models.CASCADE)


class FileGroupObjectPermission(GroupObjectPermissionBase):
    """Use a direct (non-generic) FK for group file permissions in guardian."""

    content_object = models.ForeignKey(BaseFile, related_name="group_permissions", on_delete=models.CASCADE)


BaseFileType: TypeAlias = BaseFile
