"""Custom model field validators."""

from django.core.exceptions import ValidationError


def validate_ratio(value: str) -> None:
    """Make sure ratios are expressed as x/y."""
    try:
        numerator, denominator = str(value).split("/")
    except ValueError as e:
        raise ValidationError(  # noqa: TRY003
            ("%(value)s is not a valid fraction (missing /)"),
            params={"value": value},
        ) from e
    try:
        int(numerator)
        int(denominator)
    except ValueError as e:
        raise ValidationError(  # noqa: TRY003
            ("%(value)s is not a valid fraction (numerator or denominator is not a number)"), params={"value": value}
        ) from e
