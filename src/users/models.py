"""The custom User model used in the BMA project."""

import uuid
from typing import ClassVar
from typing import TypeAlias

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from oauth2_provider.models import Application


class User(AbstractUser):  # type: ignore[django-manager-missing]
    """The custom User model used in the BMA project."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    handle = models.SlugField(
        unique=True,
        help_text="Your public BMA handle.",
    )

    display_name = models.CharField(
        max_length=100,
        default="Unnamed user",
        help_text="The display name for this user. Defaults to the BornHack users public_credit_name field.",
    )

    description = models.TextField(
        blank=True,
        help_text="A description of yourself. Supports markdown.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when this user was first created on BMA.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this user object was last updated.",
    )

    # prompt for extra fields in createsuperuser
    REQUIRED_FIELDS: ClassVar[list[str]] = ["handle", "display_name"]

    def get_absolute_url(self) -> str:
        """Return the URL for the users public profile."""
        return reverse("users:user_profile", kwargs={"user_handle": self.handle})

    @property
    def is_creator(self) -> bool:
        """Bool based on membership of settings.BMA_CREATOR_GROUP_NAME."""
        return settings.BMA_CREATOR_GROUP_NAME in self.cached_groups

    @property
    def is_moderator(self) -> bool:
        """Bool based on membership of settings.BMA_MODERATOR_GROUP_NAME."""
        return settings.BMA_MODERATOR_GROUP_NAME in self.cached_groups

    @property
    def is_curator(self) -> bool:
        """Bool based on membership of settings.BMA_CURATOR_GROUP_NAME."""
        return settings.BMA_CURATOR_GROUP_NAME in self.cached_groups

    @property
    def is_worker(self) -> bool:
        """Bool based on membership of settings.BMA_WORKER_GROUP_NAME."""
        return settings.BMA_WORKER_GROUP_NAME in self.cached_groups

    @cached_property
    def cached_groups(self) -> list[str]:
        """Optimise repeated calls to user.groups.whatever."""
        if not hasattr(self, "_cached_groups"):
            self._cached_groups = list(self.groups.values_list("name", flat=True))
        return self._cached_groups

    @property
    def webapp_oauth_client_id(self) -> str:
        """Return the client id to use for oauth for the webapp."""
        return Application.objects.get(user=self, name="autocreated-bma-webapp-client").client_id  # type: ignore[no-any-return]


UserType: TypeAlias = User
