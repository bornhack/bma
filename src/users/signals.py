"""Signal handlers for the users app."""

import logging
from typing import TYPE_CHECKING
from typing import Any

from django.conf import settings
from oauth2_provider.generators import generate_client_id
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import Application

if TYPE_CHECKING:
    from .models import User

logger = logging.getLogger("bma")


def create_webapp_oauth_app(*, sender: str, instance: "User", created: bool, **kwargs: dict[Any, Any]) -> None:
    """Create the oauth app for the BMA webapp."""
    if created and instance.username != "AnonymousUser":
        redirect_uris = [f"https://{hostname}/api/csrf/" for hostname in settings.ALLOWED_HOSTS]
        app, app_created = Application.objects.get_or_create(
            user=instance,
            redirect_uris=" ".join(redirect_uris),
            client_type="public",
            authorization_grant_type="authorization-code",
            name="autocreated-bma-webapp-client",
            skip_authorization=True,
            defaults={
                "client_id": generate_client_id(),
                "client_secret": generate_client_secret(),
            },
        )
        if app_created:
            logger.debug(f"Created webapp oauth app {app.pk} for user {instance}")
