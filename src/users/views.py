"""File views."""

import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpRequest
from django.http import HttpResponse
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic import View
from oauth2_provider.generators import generate_client_id
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import Application
from oauth2_provider.models import RefreshToken
from oauthlib.common import generate_token

from .models import User
from .models import UserType

logger = logging.getLogger("bma")


class UserProfileView(LoginRequiredMixin, DetailView):  # type: ignore[type-arg]
    """User profile view. This is the users public page."""

    template_name = "user_profile.html"
    model = User
    pk_url_kwarg = "user_uuid"
    slug_url_kwarg = "user_handle"
    slug_field = "handle"


class UserSettingsView(LoginRequiredMixin, DetailView):  # type: ignore[type-arg]
    """The users private settings page."""

    template_name = "user_settings.html"
    model = User

    def get_object(self, queryset: models.QuerySet[UserType] | None = None) -> UserType:
        """Get user from request."""
        return self.request.user  # type: ignore[return-value]


class UserSettingsUpdateView(LoginRequiredMixin, UpdateView):  # type: ignore[type-arg]
    """User settings update view."""

    template_name = "user_form.html"
    model = User
    fields = ("handle", "display_name", "description")

    def get_object(self, queryset: models.QuerySet[UserType] | None = None) -> UserType:
        """Get user from request."""
        return self.request.user  # type: ignore[return-value]


class BmaCliConfigDownloadView(LoginRequiredMixin, View):
    """Return a JSON config file for BMA CLI."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore[no-untyped-def]
        """Return the JSON config."""
        redirect_uris = [f"https://{hostname}/api/csrf/" for hostname in settings.ALLOWED_HOSTS]
        app, app_created = Application.objects.get_or_create(
            user=request.user,
            redirect_uris=" ".join(redirect_uris),
            client_type="public",
            authorization_grant_type="authorization-code",
            name="autocreated-bma-cli-client",
            skip_authorization=True,
            defaults={
                "client_id": generate_client_id(),
                "client_secret": generate_client_secret(),
            },
        )

        rt = RefreshToken.objects.create(
            user=request.user,
            token=generate_token(),
            application=app,
            token_family=uuid.uuid4(),
        )

        config = {
            "attribution": self.request.user.display_name,  # type: ignore[union-attr]
            "oauth_client_id": app.client_id,
            "refresh_token": rt.token,
            "path": "/tmp/bma",  # noqa: S108
            "bma_url": f"{self.request.scheme}://{self.request.get_host()}",
            "client_uuid": str(rt.token_family),
            "license": "CC_BY_SA_4_0",
        }
        return HttpResponse(
            json.dumps(config),
            content_type="application/json",
            headers={"content-disposition": "attachment; filename=bma_cli_config.json"},
        )
