from typing import List

from ninja import ModelSchema

from albums.models import Album


class AlbumInSchema(ModelSchema):
    """Schema for Album create operations."""

    title: str = ""
    description: str = ""
    files: List[str] = []

    class Config:
        model = Album
        model_fields = ["title", "description", "files"]


class AlbumOutSchema(ModelSchema):
    """Schema for outputting Albums in list/detail operations."""

    class Config:
        model = Album
        model_fields = "__all__"
