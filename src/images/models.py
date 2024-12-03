"""The Image model."""

from __future__ import annotations

import logging
from fractions import Fraction

# mypy: disable-error-code="var-annotated"
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from files.models import BaseFile
from files.models import ImageModel
from jobs.models import ImageConversionJob
from jobs.models import ImageExifExtractionJob
from pictures.models import PictureField
from utils.models import NP_CASCADE
from utils.models import BaseModel
from utils.upload import get_image_version_path
from utils.upload import get_mimetype_from_extension
from utils.upload import get_upload_path

if TYPE_CHECKING:
    from users.models import User

logger = logging.getLogger("bma")


class Image(BaseFile):
    """The Image model."""

    original = PictureField(
        upload_to=get_upload_path,
        max_length=255,
        width_field="width",
        height_field="height",
        help_text="The original uploaded image.",
    )

    exif = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        help_text="EXIF data for the image in JSON format.",
    )

    width = models.PositiveIntegerField(
        help_text="The width of this image (in pixels).",
    )

    height = models.PositiveIntegerField(
        help_text="The height of this image (in pixels).",
    )

    aspect_ratio = models.CharField(
        max_length=20, help_text="The aspect ratio (width/height) of the image expressed as a string like '16/9'."
    )

    pixels = models.GeneratedField(
        expression=models.F("width") * models.F("height"),
        output_field=models.PositiveBigIntegerField(),
        db_persist=True,
        help_text="The total number of pixels in this image. Useful for ordering by image size.",
    )

    def get_fullsize_version(self, mimetype: str) -> ImageVersion | None:
        """Return the ImageVersion for the fullsize version of this mimetype for this Image."""
        try:
            return self.image_versions.get(width=self.width, aspect_ratio=self.aspect_ratio, mimetype=mimetype)  # type: ignore[no-any-return]
        except ImageVersion.DoesNotExist:
            return None

    def create_jobs(self) -> None:
        """Create jobs for exif, smaller versions and thumbnails for this image."""
        if self.exif is None:
            self.create_exif_job()
        self.create_fullsize_version_jobs()
        self.create_smaller_version_jobs()
        self.create_thumbnail_jobs()

    def create_fullsize_version_jobs(self) -> None:
        """Create job to make fullsize versions of this image."""
        for filetype in settings.PICTURES["FILE_TYPES"]:  # type: ignore[attr-defined]
            # get mimetype for this extension
            mimetype = get_mimetype_from_extension(extension=filetype.lower())
            if mimetype is None:
                logger.error(f"Unable to find mimetype from extension {filetype}")
                continue
            # if this version of the file already exists bail out
            if self.get_fullsize_version(mimetype=mimetype):
                continue
            # create job for this filetype
            job, created = ImageConversionJob.objects.get_or_create(
                basefile=self,
                width=self.width,
                height=self.height,
                custom_aspect_ratio="",
                filetype=filetype,
                source_url=self.original.url,
            )

    def create_exif_job(self) -> None:
        """Create exif data extraction job."""
        # get exif data?
        job, created = ImageExifExtractionJob.objects.get_or_create(
            basefile=self,
            source_url=self.original.url,
            finished=False,
        )

    def create_smaller_version_jobs(self) -> None:
        """Create jobs to make smaller versions of this image."""
        for version in self.original.get_picture_files_list():
            # check if this file already exists
            if version.path.exists():
                continue
            # file missing, a new job must be created
            job, created = ImageConversionJob.objects.get_or_create(
                basefile=self,
                width=version.width,
                height=version.height,
                custom_aspect_ratio="" if version.aspect_ratio == Fraction(self.aspect_ratio) else version.aspect_ratio,
                filetype=version.file_type,
                source_url=self.original.url,
                finished=False,
            )

    def get_versions(
        self, mimetype: str | None = None, aspect_ratio: Fraction | None = None
    ) -> dict[Fraction | None, dict[str, dict[int, ImageVersion]]]:
        """Get image versions. Return a dict with ratio: mimetype: size: ImageVersion dicts."""
        versions = {}
        kwargs = {
            "aspect_ratio": aspect_ratio or self.aspect_ratio,
        }
        # filter by mimetype?
        if mimetype:
            kwargs["mimetype"] = mimetype
        # use requested custom AR or Image original AR
        for version in self.image_versions.filter(**kwargs):
            if version.aspect_ratio not in versions:
                versions[version.aspect_ratio] = {}
            if version.mimetype not in versions[version.aspect_ratio]:
                versions[version.aspect_ratio][version.mimetype] = {}
            versions[version.aspect_ratio][version.mimetype][version.width] = version
        return versions

    def fullsize_url(self, mimetype: str = "image/webp") -> str:
        """Return the url to the full size version of an image of the given mimetype."""
        version = self.get_fullsize_version(mimetype=mimetype)
        if version is None:
            # imageversion not found
            return ""
        return version.imagefile.url  # type: ignore[no-any-return]


class ImageVersion(ImageModel, BaseModel):
    """Model to contain smaller versions of Images."""

    job = models.OneToOneField(
        "jobs.ImageConversionJob",
        on_delete=NP_CASCADE,
        help_text="The Job which triggered uploading of this image version.",
    )

    image = models.ForeignKey(
        "images.Image",
        on_delete=NP_CASCADE,  # delete all versions when an Image is deleted
        related_name="image_versions",
        help_text="The Image this is a smaller version of.",
    )

    imagefile = PictureField(
        upload_to=get_image_version_path,
        max_length=255,
        width_field="width",
        height_field="height",
        help_text="The image version file.",
    )

    @property
    def uploader(self) -> User:
        """Return the uploader of this image version."""
        return self.job.user  # type: ignore[no-any-return]

    class Meta:
        """Meta model options for the ImageVersion model."""

        constraints = (
            # only one image of the same dimensions and mimetype at a time
            models.UniqueConstraint(fields=["image", "width", "height", "mimetype"], name="unique_image_version"),
        )
        ordering = ("-width",)
