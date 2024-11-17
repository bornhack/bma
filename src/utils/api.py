"""API related utility functions."""

import uuid
from typing import Annotated
from typing import TypeAlias

from django.db.models import QuerySet
from pydantic import BeforeValidator

from albums.models import Album
from files.models import BaseFile
from jobs.models import BaseJob

from .schema import ApiMessageSchema

# type aliases to make API return types more readable
FileApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | dict[str, BaseFile | QuerySet[BaseFile] | str]]
AlbumApiResponseType: TypeAlias = tuple[int, ApiMessageSchema | dict[str, Album | QuerySet[Album] | str]]
JobApiResponseType: TypeAlias = tuple[int, dict[str, str | QuerySet[BaseJob]]]
JobSettingsResponseType: TypeAlias = tuple[
    int, dict[str, dict[str, object | dict[str, str | dict[str, str | bool | float]]]]
]

# api field to convert from string to a comma-seperated list of UUIDs
CommaStrToUuidList = Annotated[
    list[uuid.UUID],
    BeforeValidator(lambda x: x.split(",")),
]
