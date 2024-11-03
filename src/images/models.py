"""The Image model."""
# mypy: disable-error-code="var-annotated"

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from pictures.models import PictureField

from files.models import BaseFile
from jobs.models import ImageConversionJob
from jobs.models import ImageExifExtractionJob
from utils.upload import get_upload_path


class NoPillowPictureField(PictureField):
    """A PictureField which doesn't invoke pillow."""

    def update_dimension_fields(self, instance: "Image", force: bool = False, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: ANN002,ANN003,FBT001,FBT002
        """Do nothing method to avoid trying to read the image dimensions using PIL."""


class Image(BaseFile):
    """The Image model."""

    original = NoPillowPictureField(
        upload_to=get_upload_path,
        max_length=255,
        width_field="width",
        height_field="height",
        aspect_ratios=[None, "4/3"],
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

    def create_jobs(self) -> None:
        """Create jobs for missing versions for this image."""
        # exif data
        if self.exif is None:
            job, created = ImageExifExtractionJob.objects.get_or_create(
                basefile=self,
                path=self.original.path + ".json",
            )

        # smaller versions
        for version in self.original.get_picture_files_list():
            # check if this file already exists
            if version.path.exists():
                continue
            # file missing, a new job must be created
            _, (_, filetype, ratio, _, width), _ = version.deconstruct()
            job, created = ImageConversionJob.objects.get_or_create(
                basefile=self,
                width=width,
                filetype=filetype,
                aspect_ratio_numerator=ratio.split("/")[0] if ratio else None,
                aspect_ratio_denominator=ratio.split("/")[1] if ratio else None,
                path=version.name,
            )
