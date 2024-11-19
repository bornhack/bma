"""The Image model."""

# mypy: disable-error-code="var-annotated"
from fractions import Fraction

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from files.models import BaseFile
from jobs.models import ImageConversionJob
from jobs.models import ImageExifExtractionJob
from utils.models import NoPillowPictureField
from utils.upload import get_upload_path


class Image(BaseFile):
    """The Image model."""

    original = NoPillowPictureField(
        upload_to=get_upload_path,
        max_length=255,
        width_field="width",
        height_field="height",
        help_text="The original uploaded image.",
    )

    width = models.PositiveIntegerField(
        help_text="The width of the image (in pixels).",
    )

    height = models.PositiveIntegerField(
        help_text="The height of the image (in pixels).",
    )

    exif = models.JSONField(
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
        help_text="EXIF data for the image in JSON format.",
    )

    @property
    def aspect_ratio(self) -> Fraction:
        """Return job AR as a Fraction."""
        return Fraction(self.width, self.height)

    def create_jobs(self) -> None:
        """Create jobs for exif, smaller versions and thumbnails for this image."""
        if self.exif is None:
            self.create_exif_job()
        self.create_smaller_version_jobs()
        self.create_thumbnail_jobs()

    def create_exif_job(self) -> None:
        """Create exif data extraction job."""
        # get exif data?
        job, created = ImageExifExtractionJob.objects.get_or_create(
            basefile=self,
            path=self.original.path + ".json",
        )

    def create_smaller_version_jobs(self) -> None:
        """Create jobs to make smaller versions of this image."""
        for version in self.original.get_picture_files_list():
            # check if this file already exists
            if version.path.exists():
                continue
            # file missing, a new job must be created
            _, (_, filetype, ratio, _, width), _ = version.deconstruct()
            if version.height:
                height = version.height
            else:
                height = self.calculate_version_height(width=width, ratio=ratio if ratio else self.aspect_ratio)
            job, created = ImageConversionJob.objects.get_or_create(
                basefile=self,
                path=version.name,
                width=width,
                height=height,
                custom_aspect_ratio=bool(ratio),
                filetype=filetype,
            )

    def get_image_versions(self) -> dict[str, dict[str, list[tuple[int, int, str]]]]:
        """Return versions."""
        return self.get_picturefield_versions(field=self.original)
