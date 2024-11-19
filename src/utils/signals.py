"""BMA signal handlers."""

import logging

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.signals import request_started

logger = logging.getLogger("bma")


def bma_startup(sender: WSGIHandler, **kwargs: dict[str, str]) -> None:
    """Create the BMA groups and disconnect signal."""
    logger.debug("This is the first request, running bma_startup()...")
    from django.contrib.auth.models import Group

    # create creator group if needed
    creator_group, created = Group.objects.get_or_create(name=settings.BMA_CREATOR_GROUP_NAME)
    if created:
        logger.info(f"Created creator group {settings.BMA_CREATOR_GROUP_NAME}")

    # create moderator group if needed
    moderator_group, created = Group.objects.get_or_create(name=settings.BMA_MODERATOR_GROUP_NAME)
    if created:
        logger.info(f"Created moderator group {settings.BMA_MODERATOR_GROUP_NAME}")

    # create creator group if needed
    curator_group, created = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
    if created:
        logger.info(f"Created curator group {settings.BMA_CURATOR_GROUP_NAME}")

    # create worker group if needed
    worker_group, created = Group.objects.get_or_create(name=settings.BMA_WORKER_GROUP_NAME)
    if created:
        logger.info(f"Created worker group {settings.BMA_WORKER_GROUP_NAME}")

    # all done
    logger.debug(
        "bma_startup() done, disconnecting bma_startup_signal from django.core.signals.request_started signal..."
    )
    request_started.disconnect(None, dispatch_uid="bma_startup_signal")
