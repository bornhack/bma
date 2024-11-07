"""AppConfig for the users app."""

from django.apps import AppConfig
from django.core.signals import request_started
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    """AppConfig for the users app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self) -> None:
        """Connect signal to create groups on first request."""
        from utils.signals import bma_startup

        from .models import User
        from .signals import create_webapp_oauth_app

        request_started.connect(bma_startup, dispatch_uid="bma_startup_signal")
        post_save.connect(create_webapp_oauth_app, sender=User, dispatch_uid="create_webapp_oauth_app")
