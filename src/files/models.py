"""This file contains the main BMA model BaseFile and related classes."""

# mypy: disable-error-code="var-annotated"
import logging
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
from pictures.models import PictureField
from pictures.models import PictureFieldFile
from tags.managers import BMATagManager
from tags.models import TaggedFile
from users.models import UserType
from users.sentinel import get_sentinel_user
from utils.models import NP_CASCADE
from utils.models import BaseModel
from utils.upload import get_thumbnail_path
from utils.upload import get_thumbnail_source_path

from .managers import BaseFileManager
from .managers import BaseFileQuerySet

logger = logging.getLogger("bma")

User = get_user_model()


class FileTypeChoices(models.TextChoices):
    """The filetype filter."""

    image = ("image", "Image")
    video = ("video", "Video")
    audio = ("audio", "Audio")
    document = ("document", "Document")


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


class BaseFile(PolymorphicModel):
    """The polymorphic base model inherited by the Image, Video, Audio, and Document models."""

    class Meta:
        """Define custom permissions for the BaseFile and inherited models."""

        ordering = ("created_at",)
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

    job = models.ForeignKey(
        "jobs.FileUploadJob",
        on_delete=NP_CASCADE,
        related_name="files",
        # permit nulls to make mutual job<>basefile FK work
        null=True,
        blank=True,
        help_text="The Job created when this file was uploaded.",
    )

    uploader = models.ForeignKey(
        "users.User",
        on_delete=models.SET(get_sentinel_user),
        related_name="files",
        help_text="The uploader of this file.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this object was first created.",
    )

    updated_at = models.DateTimeField(
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
        help_text="The URL to the original CC source of this work. "
        "Leave blank to consider the BMA URL the original source.",
        blank=True,
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
        help_text="The mimetype of the file as reported the uploading client. This value is read-only.",
    )

    license = models.CharField(
        max_length=20,
        choices=LicenseChoices,
        help_text="The license for this file. The license can not be changed or revoked after the file is uploaded.",
    )

    attribution = models.CharField(
        max_length=255,
        help_text="The attribution text for this file. This is usually "
        "the real name or handle of the author(s) or licensor of the file.",
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
        return reverse("files:file_show", kwargs={"file_uuid": self.pk})

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
        if hasattr(self, "thumbnailsource"):
            downloads["thumbnail_source"] = self.thumbnailsource.url
        if self.filetype == "image":
            # add download links for smaller versions of this image
            for version in self.image_versions.all():
                downloads[f"{version.width}*{version.height}"] = version.imagefile.url
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
        self.save(update_fields=[field, "updated_at"])

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
        """Create jobs to make thumbnails.

        Documents, Audios and Videos require a ThumbnailSource, Images do not.
        """
        if hasattr(self, "thumbnailsource"):
            # this file has a thumbnailsource, use that
            source = self.thumbnailsource.source
        elif self.filetype == "image":
            # create temporary thumbnailsource for job creation to get the
            # conversion rules from the thumbnail field
            source = PictureFieldFile(instance=self, field=ThumbnailSource.source.field, name=self.original.name)
        else:
            # no thumbnailsource to work with yet,
            # make sure there is a ThumbnailSourceJob
            ThumbnailSourceJob.objects.get_or_create(
                basefile=self,
                finished=False,
            )
            return
        for version in source.get_picture_files_list(exclude_oversized=False):
            # check if this file already exists
            if version.path.exists():
                continue

            # file missing, an unfinished job to create one should exist
            job, created = ThumbnailJob.objects.get_or_create(
                basefile=self,
                width=version.width,
                height=version.height,
                custom_aspect_ratio=version.aspect_ratio,
                filetype=version.file_type,
                source_url=source.url,
                finished=False,
            )
            job.full_clean()

    def get_thumbnails(self) -> dict[Fraction | None, dict[str, dict[int, "Thumbnail"]]]:
        """Return a dict with ratio: filetype: size: Thumbnail nested dicts."""
        thumbnails = {}
        for thumbnail in self.thumbnails.all():
            if thumbnail.aspect_ratio not in thumbnails:
                thumbnails[thumbnail.aspect_ratio] = {}
            if thumbnail.mimetype not in thumbnails[thumbnail.aspect_ratio]:
                thumbnails[thumbnail.aspect_ratio][thumbnail.mimetype] = {}
            thumbnails[thumbnail.aspect_ratio][thumbnail.mimetype][thumbnail.width] = thumbnail
        return thumbnails


class ImageModel(models.Model):
    """Model mixin with shared fields used by all non-polymorphic models representing images.

    The polymorphic Image model and BaseFile model share some of the same fields between them but
    polymorphic models cannot inherit from non-polymorphic models. Don't waste time trying
    to make this more DRY, find something else to do /tyk
    https://github.com/jazzband/django-polymorphic/issues/534
    """

    file_size = models.BigIntegerField(
        help_text="The size of the file in bytes. This value is read-only.",
    )

    mimetype = models.CharField(
        max_length=255,
        help_text="The mimetype of the file as reported the uploading client. This value is read-only.",
    )

    width = models.PositiveIntegerField(
        help_text="The width of this image (in pixels).",
    )

    height = models.PositiveIntegerField(
        help_text="The height of this image (in pixels).",
    )

    aspect_ratio = models.CharField(
        max_length=20,
        help_text=(
            "The intended (and advertised) aspect ratio of this image, expressed as a string "
            "like '16/9'. The actual image AR (width/height) can vary slightly "
            "from the value in this field because of rounding errors when resizing images."
        ),
    )

    pixels = models.GeneratedField(
        expression=models.F("width") * models.F("height"),
        output_field=models.PositiveBigIntegerField(),
        db_persist=True,
        help_text="The total number of pixels in this image. Useful for ordering by image size.",
    )

    class Meta:
        """This is an abstract model."""

        abstract = True


class ThumbnailSource(ImageModel, BaseModel):
    """Model to contain thumbnail sources for files.

    A ThumbnailSource is required to create Thumbnails for Video, Audio and Document
    files, but optional for Image files. If a ThumbnailSource doesn't exists for an
    Image file then the original image will be used to generate thumbnails.
    """

    job = models.OneToOneField(
        "jobs.ThumbnailSourceJob",
        on_delete=NP_CASCADE,
        help_text="The Job which triggered uploading of this ThumbnailSource.",
    )

    basefile = models.OneToOneField(
        "files.BaseFile",
        on_delete=NP_CASCADE,  # delete ThumbnailSource when a basefile is deleted
        help_text="The basefile this ThumbnailSource is for.",
    )

    source = PictureField(
        upload_to=get_thumbnail_source_path,
        max_length=255,
        width_field="width",
        height_field="height",
        aspect_ratios=["1/1", "4/3", "16/9", "2/3"],
        container_width=200,
        grid_columns=4,
        pixel_densities=[1, 2],
        help_text="The source image from which all the thumbnails are created.",
    )

    def __str__(self) -> str:
        """String representation of a thumbnailsource."""
        return (
            f"ThumbnailSource {self.uuid} {self.width}*{self.height} "
            f"{self.mimetype} for {self.basefile.filetype} {self.basefile.uuid}"
        )


class Thumbnail(ImageModel, BaseModel):
    """Model to represent thumbnails for files.

    A Thumbnail generated from a ThumbnailSource has an additional FK to the ThumbnailSource,
    where Thumbnails generated from an Image directly only has an FK to the BaseFile.
    """

    job = models.OneToOneField(
        "jobs.ThumbnailJob",
        on_delete=NP_CASCADE,
        help_text="The Job which triggered uploading of this Thumbnail.",
    )

    basefile = models.ForeignKey(
        "files.BaseFile",
        on_delete=NP_CASCADE,  # delete Thumbnails when a basefile is deleted
        related_name="thumbnails",
        help_text="The basefile this Thumbnail is for.",
    )

    source = models.ForeignKey(
        "files.ThumbnailSource",
        on_delete=NP_CASCADE,  # delete Thumbnails when ThumbnailSource is deleted
        related_name="thumbnails",
        null=True,
        blank=True,
        help_text=(
            "The ThumbnailSource this Thumbnail was generated from. This field is null "
            "if the Thumbnail was generated from the BaseFile directly (only for Image files)."
        ),
    )

    imagefile = PictureField(
        upload_to=get_thumbnail_path,
        max_length=255,
        width_field="width",
        height_field="height",
        help_text="The thumbnail file.",
    )

    class Meta:
        """Define Meta model options for the Thumbnail model."""

        constraints = (
            # only one thumbnail of the same dimensions and mimetype at a time
            models.UniqueConstraint(fields=["basefile", "width", "height", "mimetype"], name="unique_thumbnail"),
        )
        ordering = ("-width",)

    def __str__(self) -> str:
        """String representation of a thumbnail."""
        return (
            f"Thumbnail {self.uuid} {self.width}*{self.height} {self.mimetype} "
            f"for {self.basefile.filetype} {self.basefile.uuid}"
        )


class FileUserObjectPermission(UserObjectPermissionBase):
    """Use a direct (non-generic) FK for user file permissions in guardian."""

    content_object = models.ForeignKey(BaseFile, related_name="user_permissions", on_delete=NP_CASCADE)


class FileGroupObjectPermission(GroupObjectPermissionBase):
    """Use a direct (non-generic) FK for group file permissions in guardian."""

    content_object = models.ForeignKey(BaseFile, related_name="group_permissions", on_delete=NP_CASCADE)


BaseFileType: TypeAlias = BaseFile
