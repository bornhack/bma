import uuid
from typing import List

from django.urls import reverse
from ninja import Field
from ninja import ModelSchema
from ninja import Schema

from albums.models import Album
from utils.schema import ApiMessageSchema, ApiResponseSchema, ObjectPermissionSchema


class AlbumRequestSchema(ModelSchema):
    """Schema for Album create or update operations."""

    title: str = ""
    description: str = ""
    files: List[uuid.UUID] = []

    class Config:
        model = Album
        model_fields = ["title", "description", "files"]


"""Response schemas below here."""


class AlbumResponseSchema(ModelSchema):
    """Schema for outputting Albums in API operations."""

    links: dict

    class Config:
        model = Album
        model_fields = [
            "uuid",
            "owner",
            "created",
            "updated",
            "title",
            "description",
            "files",
        ]

    @staticmethod
    def resolve_links(obj, request):
        return {
            "self": reverse("api-v1-json:album_get", kwargs={"album_uuid": obj.uuid}),
        }


class SingleAlbumResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single album object."""
    response: AlbumResponseSchema


class MultipleAlbumResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple album objects."""
    response: List[AlbumResponseSchema]
