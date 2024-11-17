"""The shared filters used in the files and albums API endpoints."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.safestring import mark_safe
from ninja import FilterSchema

from .querystring import querystring_from_request

if TYPE_CHECKING:
    from django.http import HttpRequest


class SortingChoices(models.TextChoices):
    """The sorting options for files and albums."""

    title_asc = ("title_asc", "Title (ascending)")
    title_desc = ("title_desc", "Title (descending)")
    description_asc = ("description_asc", "Description (ascending)")
    description_desc = ("description_desc", "Description (descending)")
    created_asc = ("created_asc", "Created (ascending)")
    created_desc = ("created_desc", "Created (descending)")
    updated_asc = ("updated_asc", "Updated (ascending)")
    updated_desc = ("updated_desc", "Updated (descending)")


class ListFilters(FilterSchema):
    """Filters shared between the file_list, album_list, job_list, and user_list API endpoints."""

    limit: int = 100
    offset: int | None = None
    search: str | None = None
    sorting: SortingChoices | None = None


def filter_button(text: str, request: "HttpRequest", **kwargs: str) -> str:
    """Add a filter button before the provided text with a querystring updated with the provided kwargs."""
    querystring = querystring_from_request(request=request, **kwargs)
    button = f'<a href="{request.path}{querystring}"><i class="fas fa-filter"></i></a>'
    return mark_safe(f"{button}&nbsp;{text}")  # noqa: S308
