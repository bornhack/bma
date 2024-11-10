"""Add BMA version to request context."""

from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.http import HttpRequest


def bma_version(request: "HttpRequest") -> dict[str, str]:
    """Add the BMA version to the request context."""
    return {"bma_version": settings.BMA_VERSION}
