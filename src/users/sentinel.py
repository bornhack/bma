"""This module contains code to create or return a 'sentinel user' to use in place of deleted users."""

from django.contrib.auth import get_user_model

User = get_user_model()


def get_sentinel_user() -> User:  # type: ignore[valid-type]
    """Used in on_delete of FK relations to the user model (default users.models.User)."""
    return User.objects.get_or_create(username="deleted")[0]
