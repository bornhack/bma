"""File views."""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import DetailView
from django.views.generic import UpdateView

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
    fields = ("display_name", "description")

    def get_object(self, queryset: models.QuerySet[UserType] | None = None) -> UserType:
        """Get user from request."""
        return self.request.user  # type: ignore[return-value]
