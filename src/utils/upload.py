"""Upload related utilities."""

from pathlib import Path

from files.models import BaseFile


def get_upload_path(instance: BaseFile, filename: str) -> Path:
    """Return the upload path under MEDIA_ROOT for this file. Used by models with filefields."""
    # return something like
    # user_dbd9d175-7a54-4339-b46d-de87791cb188/image/bma_image_6fcfaf74-3b39-4443-889e-93fc7bf8627b.jpg
    return Path(
        f"user_{instance.uploader.uuid}/{instance.filetype}/bma_{instance.filetype}_{instance.uuid}{Path(filename).suffix.lower()}",
    )
