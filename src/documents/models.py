"""The Document model."""

from django.db import models

from files.models import BaseFile
from utils.storage import BmaFileSystemStorage
from utils.upload import get_upload_path


class Document(BaseFile):  # type: ignore[django-manager-missing]
    """The Document model."""

    original = models.FileField(
        storage=BmaFileSystemStorage,
        upload_to=get_upload_path,
        max_length=255,
        help_text="The original uploaded document file.",
    )
