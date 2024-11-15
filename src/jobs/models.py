"""Models to manage file processing jobs handled by clients."""

# mypy: disable-error-code="var-annotated"
import uuid
from fractions import Fraction

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from polymorphic.models import PolymorphicModel

from utils.upload import get_thumbnail_source_path


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

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="The unique ID (UUID4) of this object.",
    )

    basefile = models.ForeignKey(
        "files.BaseFile",
        on_delete=models.CASCADE,  # delete jobs when a file is deleted
        related_name="jobs",
    )

    created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this job was first created.",
    )

    updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this job was last updated.",
    )

    path = models.CharField(
        max_length=255,
        help_text="Path under MEDIA_ROOT for the result of the file processing job.",
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

    @property
    def source_url(self) -> str:
        """Return the URL of the source file to use for this job. Overridden on some job types."""
        return str(self.basefile.resolve_links()["downloads"]["original"])

    @property
    def source_filename(self) -> str:
        """Return the URL of the source file to use for this job. Overridden on some job types."""
        return str(self.basefile.filename)


class ImageConversionJob(BaseJob):
    """Model to contain image conversion jobs."""

    width = models.PositiveIntegerField(help_text="The desired width of the converted image.")

    height = models.PositiveIntegerField(help_text="The desired height of the converted image.")

    filetype = models.CharField(
        max_length=10,
        validators=[validate_image_filetype],
        help_text="The desired file type for this job.",
    )

    custom_aspect_ratio = models.BooleanField(
        default=False,
        help_text="True if this job needs cropping to a custom AR, False if no crop is needed.",
    )

    @property
    def aspect_ratio(self) -> Fraction:
        """Return job AR as a Fraction."""
        return Fraction(self.width, self.height)

    @property
    def mimetype(self) -> str:
        """Get the value for the mimetype field."""
        for mimetype, extension in settings.ALLOWED_IMAGE_TYPES.items():
            if self.filetype.lower() == extension:
                return mimetype
        raise FiletypeUnsupportedError(filetype=self.filetype)


class ImageExifExtractionJob(BaseJob):
    """Model to contain image exif exctraction jobs. No extra fields."""


class ThumbnailSourceJob(BaseJob):
    """Model to contain thumbnail source jobs. No extra fields."""


class ThumbnailJob(ImageConversionJob):
    """Model to contain image thumbnail jobs. No extra fields."""

    @property
    def source_url(self) -> str:
        """Return the URL of the source file to use for this job."""
        return str(self.basefile.resolve_links()["downloads"].get("thumbnail_source", ""))

    @property
    def source_filename(self) -> str:
        """Return the filename of the source file to use for this job."""
        return get_thumbnail_source_path(instance=self.basefile.thumbnail, filename="notused").name
