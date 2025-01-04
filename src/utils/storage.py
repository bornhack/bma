"""BMA specific FileSystemStorage subclass with shorteruuid urls."""

import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.files.storage import FileSystemStorage

if TYPE_CHECKING:
    from django.core.handlers.wsgi import WSGIHandler


logger = logging.getLogger("bma")


class BmaFileSystemStorage(FileSystemStorage):
    """FileSystemStorage subclass with shorter urls.

    BMA file serving is done using a prefix based on the class of file. The path under
    settings.MEDIA_URL is:
      - /oi/shortuuid.ext for original Image files
      - /ov/shortuuid.ext for original Video files
      - /oa/shortuuid.ext for original Audio files
      - /od/shortuuid.ext for original Document files
      - /ts/shortuuid.ext for ThumbnailSource files
      - /iv/shortuuid.ext for ImageVersion files (smaller versions of original images)
      - /t/shortuuid.ext for Thumbnail files

    Local paths are documented in the utils.upload.get_*_path functions.
    """

    def url(self, name: str | None) -> str:
        """Return the external URL for this file, using shortuuid and prefix."""
        if name is None:
            return ""
        # does the file exist on disk?
        if not self.exists(name):
            return ""

        # split file path into parts
        parts = name.split("/")

        try:
            if re.match(
                r"^user_[2-9A-HJ-NP-Za-km-z]{22}\/\w+\/bma_\w+_[2-9A-HJ-NP-Za-km-z]{22}\.\w+$",
                name,
            ):
                # file is an original
                user, filetype, filename = parts
                pk = filename.split(".")[0].split("_")[2]
                prefix = f"o{filetype[0]}"

            elif re.match(
                r"^user_[2-9A-HJ-NP-Za-km-z]{22}\/\w+\/bma_\w+_[2-9A-HJ-NP-Za-km-z]{22}\/thumbnailsource_[2-9A-HJ-NP-Za-km-z]{22}\.\w+",
                name,
            ):
                # file is a thumbnailsource
                user, filetype, filedir, filename = parts
                pk = filename.split(".")[0].split("_")[1]
                prefix = "ts"

            elif re.match(
                r"^user_[2-9A-HJ-NP-Za-km-z]{22}\/image\/bma_image_[2-9A-HJ-NP-Za-km-z]{22}\/\w+\/[2-9A-HJ-NP-Za-km-z]{22}_\d+w\.\w+",
                name,
            ):
                # file is an imageversion
                user, filetype, filedir, aspectratio, filename = parts
                pk = filename.split(".")[0].split("_")[2]
                prefix = "iv"

            elif re.match(
                r"^user_[2-9A-HJ-NP-Za-km-z]{22}\/\w+\/bma_\w+_[2-9A-HJ-NP-Za-km-z]{22}\/thumbnails\/\w+\/[2-9A-HJ-NP-Za-km-z]{22}_\d+w\.\w+",
                name,
            ):
                # file is a thumbnail
                user, filetype, filedir, _, aspectratio, filename = parts
                pk = filename.split(".")[0].split("_")[2]
                prefix = "t"

            else:
                # unknown
                logger.debug(f"Unknown file class {name}")
                return ""
        except IndexError:
            # something is fucky
            logger.debug(f"Cannot parse filename {name}")
            return ""

        # get extension
        _, extension = filename.split(".")

        # all good
        return f"{self.base_url}{prefix}/{pk}.{extension}"


def clean_empty_mediaroot_subdirs(sender: "WSGIHandler", **kwargs: dict[str, str]) -> None:
    r"""Delete empty subdirs under MEDIA_ROOT.

    Intended as a python implementation of:
      `find /path/to/django_media_root/ -depth -mindepth 1 -type d -exec rmdir {} \;`
    """
    recurse = False
    for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False):
        # remove dir if it is empty and not the MEDIA_ROOT
        if root != str(settings.MEDIA_ROOT) and not dirs and not files:
            Path(root).rmdir()
            recurse = True
    # Run again to delete now empty dirs (if any)
    if recurse:
        clean_empty_mediaroot_subdirs(sender=sender, **kwargs)
