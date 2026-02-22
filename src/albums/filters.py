"""The filters used for album list endpoints."""

import uuid
from typing import ClassVar

import django_filters

from utils.filters import FileAlbumSortingChoices
from utils.filters import ListFilters

from .models import Album


class AlbumFilters(ListFilters):
    """The filters used for the album_list django-ninja API endpoint."""

    files: list[uuid.UUID] | None = None
    sorting: FileAlbumSortingChoices | None = None


class AlbumFilter(django_filters.FilterSet):
    """The Album filter used by django-filters."""

    class Meta:
        """Set model and fields."""

        model = Album
        fields: ClassVar[dict[str, list[str]]] = {
            "title": ["exact", "icontains"],
            "description": ["icontains"],
        }
