"""Models to manage file processing jobs handled by clients."""
# mypy: disable-error-code="var-annotated"

import logging
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from ninja.files import UploadedFile
from polymorphic.models import PolymorphicModel

from utils.models import NP_CASCADE
from utils.polymorphic_related import RelatedPolymorphicManager

from .managers import JobManager

logger = logging.getLogger("bma")


def validate_image_filetype(value: str) -> None:
    """Make sure ImageConversionJob instances use filetypes we support."""
    if value not in settings.PICTURES["FILE_TYPES"]:  # type: ignore[operator]
        raise ValidationError(f"The filetype '{value}' is not an enabled django-pictures filetype in settings.")  # noqa: TRY003


class FiletypeUnsupportedError(Exception):
    """Exception raised when an unsupported filetype is used."""

    def __init__(self, filetype: str) -> None:
        """Exception raised when an unsupported filetype is used."""
        super().__init__(f"Unsupported filetype: {filetype}")


#################### JOBS #########################################


class BaseJob(PolymorphicModel):
    """Base model to represent file processing jobs."""

    objects = RelatedPolymorphicManager()

    bmanager = JobManager()

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    basefile = models.ForeignKey(
        "files.BaseFile",
        on_delete=NP_CASCADE,  # delete jobs when a file is deleted
        related_name="jobs",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this job was first created.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this job was last updated.",
    )

    source_url = models.CharField(
        max_length=255,
        help_text="URL to the source file to use for this job.",
    )

    user = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # set job user to null if the user is deleted
        related_name="assigned_jobs",
        help_text="The user who is handling the job.",
    )

    client_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="The UUID4 of the client instance/thread handling the job.",
    )

    client_version = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Text description of the client handling this job.",
    )

    finished = models.BooleanField(
        default=False,
        editable=False,
        help_text="A job will be marked as finished when the job result has been received.",
    )

    @property
    def job_type(self) -> str:
        """Use class name as job type."""
        return self.__class__.__name__


class FileUploadJob(BaseJob):
    """Model to contain file upload jobs. File upload jobs are created on upload. No extra fields."""

    def result_url(self) -> str:
        """Return the result url."""
        # the basefile model doesn't have the .original field so this is a bit awkward
        return str(self.basefile.get_real_instance().original.url)


class ImageJob(BaseJob):
    """Fields shared between ThumbnailJobs and ImageConversionJobs."""

    width = models.PositiveIntegerField(help_text="The desired width of the converted image.")

    height = models.PositiveIntegerField(help_text="The desired height of the converted image.")

    filetype = models.CharField(
        max_length=10,
        validators=[validate_image_filetype],
        help_text="The desired file type of the converted image.",
    )

    custom_aspect_ratio = models.CharField(
        max_length=20,
        blank=True,
        help_text="Specifies the desired aspect ratio of the converted image. "
        "Blank if the AR of the source image is to be maintained. Used by the converting "
        "client to decide on resize method (crop or maintain ratio) and by the "
        "server to create the ImageVersion/Thumbnail object correctly when the "
        "result is uploaded.",
    )

    class Meta:
        """Abstract model."""

        abstract = True

    @property
    def mimetype(self) -> str:
        """Get the value for the mimetype field."""
        for mimetype, extension in settings.ALLOWED_IMAGE_TYPES.items():
            if self.filetype.lower() == extension:
                return mimetype
        raise FiletypeUnsupportedError(filetype=self.filetype)


class ImageConversionJob(ImageJob):
    """Model to contain image conversion jobs."""

    def handle_result(self, f: UploadedFile, data: dict[str, str]) -> None:
        """Save the result of an ImageConversionJob."""
        from images.models import ImageVersion

        # create model instance
        image = ImageVersion(
            job=self,
            image=self.basefile,
            # use AR from source image if no custom AR is requested
            aspect_ratio=self.custom_aspect_ratio or self.basefile.aspect_ratio,
            imagefile=f,
            file_size=f.size,  # type: ignore[misc]
            **data,
        )

        # validate
        image.full_clean()

        # delete any existing version of this image with this size and mimetype before saving
        ImageVersion.objects.filter(
            image=self.basefile, width=image.width, height=image.height, mimetype=image.mimetype
        ).delete()

        # save the imageversion
        image.save()

        # a bit of output
        logger.debug(
            f"{self.job_type} {self.pk} wrote {f.size} bytes {self.width}x{self.height}"
            f"{image.mimetype} image {image.uuid} to {image.imagefile.path}"
        )

    def result_url(self) -> str:
        """Return the result url."""
        return str(self.imageversion.imagefile.url)


class ImageExifExtractionJob(BaseJob):
    """Model to contain image exif exctraction jobs. No extra fields."""

    def result_url(self) -> str:
        """Return the result url."""
        return str(self.basefile.get_absolute_url())


class ThumbnailSourceJob(BaseJob):
    """Model to contain thumbnail source jobs. No extra fields."""

    def handle_result(self, f: UploadedFile, data: dict[str, str]) -> None:
        """Handle the result of a ThumbnailSourceJob."""
        from files.models import ThumbnailSource

        # delete any existing ThumbnailSource for this file
        ts = ThumbnailSource(  # type: ignore[misc]
            job=self,
            basefile=self.basefile,
            source=f,
            file_size=f.size,
            **data,
        )

        # validate
        ts.full_clean()

        # delete existing source
        ThumbnailSource.objects.filter(basefile=self.basefile).delete()

        # save and create jobs
        ts.save()
        self.basefile.create_thumbnail_jobs()

        # log message and return
        logger.debug(
            f"{self.job_type} {self.pk} wrote {f.size} bytes {self.width}x{self.height}"
            f"{self.mimetype} thumbnailsource {ts.uuid} to {ts.source.path}"
        )

    def result_url(self) -> str:
        """Return the result url."""
        return str(self.thumbnailsource.source.url)


class ThumbnailJob(ImageJob):
    """Model to contain image thumbnail jobs. No extra fields."""

    def handle_result(self, f: UploadedFile, data: dict[str, str]) -> None:
        """Save the result of a ThumbnailJob as a Thumbnail object."""
        from files.models import Thumbnail

        # set thumbnailsource FK?
        if hasattr(self.basefile, "thumbnailsource") and self.source_url != self.basefile.thumbnailsource.source.url:
            data["source"] = self.basefile.thumbnailsource
        elif self.source_url != self.basefile.original.url:
            # source not basefile and not current thumbnailsource, bail out
            raise ValidationError("Source")
        thumb = Thumbnail(
            job=self,
            basefile=self.basefile,
            aspect_ratio=self.custom_aspect_ratio,
            imagefile=f,
            file_size=f.size,  # type: ignore[misc]
            **data,
        )

        # validate
        thumb.full_clean()

        # delete existing thumbnail of this size and type
        Thumbnail.objects.filter(
            basefile=self.basefile, width=data["width"], height=data["height"], mimetype=data["mimetype"]
        ).delete()

        # save thumbnail
        thumb.save()

        # and log message
        logger.debug(
            f"{self.job_type} {self.pk} wrote {f.size} bytes {self.width}x{self.height}"
            f"{self.mimetype} thumbnail {thumb.pk} to {thumb.imagefile.path}"
        )

    def result_url(self) -> str:
        """Return the result url."""
        return str(self.thumbnail.imagefile.url)
