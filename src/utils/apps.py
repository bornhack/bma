"""AppConfig for the utils app."""

from django.apps import AppConfig
from django_cleanup.signals import cleanup_post_delete

from utils.storage import clean_empty_mediaroot_subdirs


class UtilsConfig(AppConfig):
    """AppConfig for the utils app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "utils"

    def ready(self) -> None:
        """Connect signal to delete empty MEDIA_ROOT subdirs after file deletes."""
        cleanup_post_delete.connect(clean_empty_mediaroot_subdirs)
