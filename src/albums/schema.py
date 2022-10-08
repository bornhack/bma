import uuid
from typing import List

from django.urls import reverse
from ninja import Field
from ninja import ModelSchema
from ninja import Schema

from albums.models import Album
from utils.schema import ListFilters


class AlbumInSchema(ModelSchema):
    """Schema for Album create operations."""

    title: str = ""
    description: str = ""
    files: List[str] = []

    class Config:
        model = Album
        model_fields = ["title", "description", "files"]


class LinkSchema(Schema):
    self: str = None


class AlbumOutSchema(ModelSchema):
    """Schema for outputting Albums in list/detail operations."""

    links: LinkSchema

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

    def resolve_links(self, obj):
        return {
            "self": reverse("api-v1-json:album_get", kwargs={"album_uuid": obj.uuid}),
        }


class AlbumFilters(ListFilters):
    """The filters used for the album_list endpoint."""

    files: List[uuid.UUID] = Field(None, alias="files")
