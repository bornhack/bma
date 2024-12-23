"""This module contains code to create or return a 'sentinel user' to use in place of deleted users."""

import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger("bma")
User = get_user_model()


def get_deleted_user() -> User:  # type: ignore[valid-type]
    """Used in on_delete of FK relations to the user model (default users.models.User)."""
    user, created = User.objects.get_or_create(
        uuid="00000000-0000-0000-0000-000000000000",
        username="deleted",
        handle="deleted",
        display_name="Deleted user",
        description="This user has been deleted.",
    )
    if created:
        logger.info(f"Created deleted user {user}")
    return user


def get_system_user() -> User:  # type: ignore[valid-type]
    """Used in FK relations to the user model when the system did something, e.g. initial perms."""
    user, created = User.objects.get_or_create(
        uuid="00000000-0000-0000-0000-000000000001",
        username="system",
        handle="system",
        display_name="BMA System User",
        description="This user is internal to BMA. It does not represent a real person.",
    )
    if created:
        logger.info(f"Created system user {user}")
    return user
