"""Field validators."""

from django.core.exceptions import ValidationError


def validate_thumbnail_url(value: str) -> None:
    """Make sure thumbnail URLs are local relative URLs under /static/images/ or /media/."""
    if not value.startswith("/static/images/") and not value.startswith("/media/"):
        raise ValidationError("non-local")
