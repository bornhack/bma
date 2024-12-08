"""The Image model."""

import logging
import zoneinfo
from datetime import datetime
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

    def get_fullsize_version(self, mimetype: str) -> "ImageVersion | None":
        """Return the ImageVersion for the fullsize version of this mimetype for this Image.

        Performance sensitive, called from template tags, do not break prefetching. Loop over
        self.image_version_list instead of self.image_versions.filter().
        """
        for image in self.image_version_list:
            if image.width == self.width and image.aspect_ratio == self.aspect_ratio and image.mimetype == mimetype:
                return image  # type: ignore[no-any-return]
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
    ) -> dict[Fraction | None, dict[str, dict[int, "ImageVersion"]]]:
        """Get image versions. Return a dict with ratio: mimetype: size: ImageVersion dicts.

        Performance sensitive, called from template tags, do not break prefetching. Loop over
        self.image_version_list instead of self.image_versions.filter().
        """
        versions = {}
        kwargs = {
            "aspect_ratio": aspect_ratio or self.aspect_ratio,
        }
        # filter by mimetype?
        if mimetype:
            kwargs["mimetype"] = mimetype
        # use requested custom AR or Image original AR
        for version in self.image_version_list:
            if version.aspect_ratio != kwargs["aspect_ratio"]:
                continue
            if "mimetype" in kwargs and version.mimetype != kwargs["mimetype"]:
                continue
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

    def get_exif_value(self, idf: str, key: str) -> str:
        """Get an exif value from exif data."""
        if not self.exif or idf not in self.exif or key not in self.exif[idf]:
            return ""
        return self.exif[idf][key]  # type: ignore[no-any-return]

    def get_exif_camera(self) -> str:
        """Get camera make and model from exif data."""
        make = self.get_exif_value(idf="Image", key="Make")
        model = self.get_exif_value(idf="Image", key="Model")
        if make and model:
            return f"{make} {model}"
        if make:
            return make
        if model:
            return model
        return ""

    def get_exif_lens(self) -> str:
        """Get lens info from exif data."""
        return self.get_exif_value(idf="EXIF", key="LensModel")

    def get_exif_focal(self) -> str:
        """Get focal length from exif data."""
        return self.get_exif_value(idf="EXIF", key="FocalLength")

    def get_exif_shutter(self) -> str:
        """Get shutter speed from exif data."""
        shutter = self.get_exif_value(idf="EXIF", key="ExposureTime")
        if not shutter:
            return ""
        exptime = Fraction(shutter)
        if exptime.denominator == 0:
            return ""
        return f"{exptime} s"

    def get_exif_iso(self) -> str:
        """Get iso speed from exif data."""
        return self.get_exif_value(idf="EXIF", key="ISOSpeedRatings")

    def get_exif_createtime(self) -> datetime | str:
        """Get date taken from exif data."""
        odt = self.get_exif_value(idf="EXIF", key="DateTimeOriginal")
        if not odt:
            return ""
        # is there an OffsetTime?
        ot = self.get_exif_value(idf="EXIF", key="OffsetTime")
        if ot:
            return datetime.strptime(f"{odt} {ot}", "%Y:%m:%d %H:%M:%S %z")
        return datetime.strptime(odt, "%Y:%m:%d %H:%M:%S").replace(tzinfo=zoneinfo.ZoneInfo(settings.TIME_ZONE))

    def get_exif_fstop(self) -> float | str:
        """Get f-stop value from exif data."""
        fn = self.get_exif_value(idf="EXIF", key="FNumber")
        if not fn:
            return ""
        return round(float(Fraction(fn)), 1)

    def get_exif_orientation(self) -> str:
        """Get orientation from exif data."""
        return self.get_exif_value(idf="EXIF", key="Orientation")


class ImageVersion(ImageModel, BaseModel):
    """Model to contain smaller versions of Images."""

    job = models.OneToOneField(
        "jobs.ImageConversionJob",
        on_delete=NP_CASCADE,
        help_text="The Job which triggered uploading of this image version.",
    )

    # This FK points to BaseFile instead of Image to make prefetching ImageVersions possible.
    image = models.ForeignKey(
        "files.BaseFile",
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
    def uploader(self) -> "User":
        """Return the uploader of this image version."""
        return self.job.user  # type: ignore[no-any-return]

    class Meta:
        """Meta model options for the ImageVersion model."""

        constraints = (
            # only one image of the same dimensions and mimetype at a time
            models.UniqueConstraint(fields=["image", "width", "height", "mimetype"], name="unique_image_version"),
        )
        ordering = ("-width",)
