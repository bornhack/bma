"""Schemas for album API calls."""

import uuid
from collections.abc import Sequence

from django.http import HttpRequest
from django.urls import reverse
from ninja import ModelSchema

from albums.models import Album
from utils.schema import ApiResponseSchema


class AlbumRequestSchema(ModelSchema):
    """Schema for Album create or update operations."""

    title: str = ""
    description: str = ""
    files: Sequence[uuid.UUID] = []

    class Config:
        """Set model and fields."""

        model = Album
        model_fields = ("title", "description", "files")


"""Response schemas below here."""


class AlbumResponseSchema(ModelSchema):
    """Schema for outputting Albums in API operations."""

    links: dict[str, str | dict[str, str]]
    files: Sequence[uuid.UUID] = []

    class Config:
        """Set model and fields."""

        model = Album
        model_fields = (
            "uuid",
            "owner",
            "created",
            "updated",
            "title",
            "description",
            "files",
        )

    @staticmethod
    def resolve_links(obj: Album, context: dict[str, HttpRequest]) -> dict[str, str | dict[str, str]]:
        """For now only a self and detail link for albums."""
        return {
            "self": reverse("api-v1-json:album_get", kwargs={"album_uuid": obj.uuid}),
            "detail": reverse("albums:album_detail", kwargs={"album_uuid": obj.uuid}),
        }

    @staticmethod
    def resolve_files(obj: Album, context: dict[str, HttpRequest]) -> list[str]:
        """Only get active memberships."""
        return [str(f.pk) for f in obj.active_files_list]


class SingleAlbumResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single album object."""

    bma_response: AlbumResponseSchema


class MultipleAlbumResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple album objects."""

    bma_response: list[AlbumResponseSchema]
