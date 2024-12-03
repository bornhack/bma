"""AppConfig for the pictures app."""

from django.apps import AppConfig


class PicturesAppConfig(AppConfig):
    """AppConfig for the pictures app."""

    name = "pictures"

    def ready(self) -> None:
        """AppConfig for the pictures app."""
