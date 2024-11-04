"""API related utility functions."""

from typing import TypeAlias

from django.db.models import QuerySet

from albums.models import Album
from files.models import BaseFile
from jobs.models import BaseJob

from .schema import ApiMessageSchema

# type aliases to make API return types more readable
FileApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | dict[str, BaseFile | QuerySet[BaseFile] | str]]
AlbumApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | dict[str, Album | QuerySet[Album] | str]]
JobApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | QuerySet[BaseJob]]
JobSettingsResponseType: TypeAlias = tuple[
    int, dict[str, dict[str, dict[str, list[tuple[str, str]] | dict[str, dict[str, str]]]]]
]
