"""Upload related utilities."""

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from files.models import BaseFile
    from files.models import Thumbnail
    from files.models import ThumbnailSource
    from images.models import ImageVersion


def get_extension_from_mimetype(mimetype: str) -> str:
    """Find the preferred extension for a mimetype in settings."""
    # get extension based on mimetype
    if mimetype in settings.ALLOWED_IMAGE_TYPES:
        return settings.ALLOWED_IMAGE_TYPES[mimetype]
    if mimetype in settings.ALLOWED_VIDEO_TYPES:
        return settings.ALLOWED_VIDEO_TYPES[mimetype]
    if mimetype in settings.ALLOWED_AUDIO_TYPES:
        return settings.ALLOWED_AUDIO_TYPES[mimetype]
    if mimetype in settings.ALLOWED_DOCUMENT_TYPES:
        return settings.ALLOWED_DOCUMENT_TYPES[mimetype]
    raise ValueError(mimetype)


def get_mimetype_from_extension(extension: str) -> str | None:
    """Return mimetype for the extension using pythons mimetypes module."""
    mimetype, _encoding = mimetypes.guess_type(url=f"foo.{extension}", strict=False)
    return mimetype


def get_upload_path(instance: "BaseFile", filename: str) -> Path:
    """Return the upload path under MEDIA_ROOT for this file. Used by models with filefields."""
    # return something like
    # user_dbd9d175-7a54-4339-b46d-de87791cb188/image/bma_image_6fcfaf74-3b39-4443-889e-93fc7bf8627b.jpg
    extension = get_extension_from_mimetype(mimetype=instance.mimetype)
    return Path(
        # put the file under a user-specific dir
        f"user_{instance.uploader.uuid}",
        # and under a filetype-specific dir (image, video, audio, or document)
        instance.filetype,
        # with a filename including the filetype and uuid and
        # the preferred extension for this mimetype from settings
        f"bma_{instance.filetype}_{instance.uuid}.{extension}",
    )


def get_thumbnail_source_path(instance: "ThumbnailSource", filename: str) -> Path:
    """Return the upload path under MEDIA_ROOT for the thumbnail source file.

    The actual thumbnails will be saved in the same directory.
    """
    extension = get_extension_from_mimetype(mimetype=instance.mimetype)
    return Path(
        # put under a user-specific dir
        f"user_{instance.basefile.uploader.uuid}",
        # and under a filetype-specific dir (image, video, audio, or document)
        instance.basefile.filetype,
        # under a file-specific dir (same place smaller image versions are saved)
        f"bma_{instance.basefile.filetype}_{instance.basefile.uuid}",
        # in a file named thumbnail with the proper extension
        f"thumbnail.{extension}",
    )


def get_thumbnail_path(instance: "Thumbnail", filename: str = "") -> Path:
    """Return the upload path under MEDIA_ROOT for this Thumbnail.

    The filename argument is not used.
    """
    # return something like
    # user_dbd9d175-7a54-4339-b46d-de87791cb188/image/bma_image_6fcfaf74-3b39-4443-889e-93fc7bf8627b/thumbnail/400w.webp
    extension = get_extension_from_mimetype(mimetype=instance.mimetype)
    return Path(
        # put the file under a user-specific dir
        f"user_{instance.job.user.uuid}",
        # and under a filetype-specific dir (image, video, audio, or document)
        instance.basefile.filetype,
        # with a filename including the filetype and uuid and
        # the preferred extension for this mimetype from settings
        f"bma_{instance.basefile.filetype}_{instance.basefile.uuid}",
        # inside the thumbnail folder
        "thumbnail",
        # inside an AR folder if needed
        f"{instance.aspect_ratio.replace('/', '_')}" if instance.aspect_ratio else "",
        # with a filename like 400w.webp
        f"{instance.width}w.{extension}",
    )


def get_image_version_path(instance: "ImageVersion", filename: str) -> Path:
    """Return the upload path under MEDIA_ROOT for this ImageVersion."""
    # return something like
    # user_dbd9d175-7a54-4339-b46d-de87791cb188/image/bma_image_6fcfaf74-3b39-4443-889e-93fc7bf8627b/400w.webp
    extension = get_extension_from_mimetype(mimetype=instance.mimetype)
    return Path(
        # put the file under a user-specific dir
        f"user_{instance.uploader.uuid}",
        # and under a filetype-specific dir (image in this case)
        "image",
        # with a filename including the filetype and uuid and
        # the preferred extension for this mimetype from settings
        f"bma_image_{instance.image.uuid}",
        # inside an AR folder if needed
        f"{instance.aspect_ratio.replace('/', '_')}" if instance.aspect_ratio else "",
        # with a filename like 400w.webp
        f"{instance.width}w.{extension}",
    )
