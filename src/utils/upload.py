from pathlib import Path


def get_upload_path(instance, filename):
    """Return the upload path under MEDIA_ROOT for this file."""
    return Path(
        f"user_{instance.owner.id}/{instance.filetype}/bma_{instance.filetype}_{instance.uuid}{Path(filename).suffix.lower()}",
    )
