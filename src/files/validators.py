from django.core.exceptions import ValidationError


def validate_thumbnail_url(value):
    if not value.startswith("/static/") and not value.startswith("/media/"):
        raise ValidationError(f"{value} is not a valid local url")
