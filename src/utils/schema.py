from django.db import models
from ninja import Schema


class SortingChoices(models.TextChoices):
    """The sorting options."""

    title_asc = ("title_asc", "Title (ascending)")
    title_desc = ("title_desc", "Title (descending)")
    description_asc = ("description_asc", "Description (ascending)")
    description_desc = ("description_desc", "Description (descending)")
    created_asc = ("created_asc", "Created (ascending)")
    created_desc = ("created_desc", "Created (descending)")
    updated_asc = ("updated_asc", "Updated (ascending)")
    updated_desc = ("updated_desc", "Updated (descending)")


class ListFilters(Schema):
    """Filters shared between the file_list and album_list endpoints."""

    limit: int = 100
    offset: int = None
    search: str = None
    sorting: SortingChoices = None


class MessageSchema(Schema):
    """The schema used for all API messages."""

    message: str
    details: dict = None
