"""The filters used for album list endpoints."""

import uuid
from typing import TYPE_CHECKING
from typing import ClassVar

import django_filters
from django.utils import timezone
from ninja import Field

from files.models import BaseFile
from utils.filters import ListFilters

from .models import Album

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest


class AlbumFilters(ListFilters):
    """The filters used for the album_list django-ninja API endpoint."""

    files: list[uuid.UUID] = Field(None, alias="files")


def get_permitted_files(request: "HttpRequest") -> "QuerySet[BaseFile]":
    """Called by AlbumFilter to get files for the albumlist filter multiselect form field."""
    return BaseFile.bmanager.get_permitted(user=request.user).all()  # type: ignore[no-any-return]


class AlbumFilter(django_filters.FilterSet):
    """The Album filter used by django-filters."""

    # when filtering by files only show files the user has permission for in the form
    files = django_filters.filters.ModelMultipleChoiceFilter(
        field_name="files",
        queryset=get_permitted_files,
        method="filter_files",
    )

    def filter_files(self, queryset: "QuerySet[Album]", name: str, value: str) -> "QuerySet[Album]":
        """When filtering by files only consider currently active memberships."""
        # we want AND so loop over files and filter for each,
        # finally returning only albums containing all the files in value
        for f in value:
            queryset = queryset.filter(memberships__basefile__in=[f], memberships__period__contains=timezone.now())
        return queryset

    class Meta:
        """Set model and fields."""

        model = Album
        fields: ClassVar[dict[str, list[str]]] = {
            "title": ["exact", "icontains"],
            "description": ["icontains"],
        }
