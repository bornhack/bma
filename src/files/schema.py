import uuid
from pathlib import Path
from typing import List
from typing import Optional

from ninja import Field
from ninja import ModelSchema

from albums.schema import AlbumOutSchema
from files.models import BaseFile
from utils.license import LicenseChoices
from utils.schema import ListFilters
from utils.schema import SortingChoices


class UploadMetadata(ModelSchema):
    """File metatata."""

    license: LicenseChoices
    # title, description and source are optional
    title: str = ""
    description: str = ""
    source: str = ""

    class Config:
        model = BaseFile
        model_fields = ["license", "attribution", "title", "description", "source"]


class FileOutSchema(ModelSchema):
    albums: List[AlbumOutSchema]
    filename: str
    url: str

    class Config:
        model = BaseFile
        model_fields = "__all__"

    def resolve_filename(self, obj):
        return Path(obj.original.path).name

    def resolve_url(self, obj):
        return obj.original.url


class FileUpdateSchema(ModelSchema):
    title: Optional[str] = ""
    description: Optional[str] = ""
    source: Optional[str] = ""
    license: Optional[str] = ""
    attribution: Optional[str] = ""

    class Config:
        model = BaseFile
        model_fields = ["title", "description", "source", "license", "attribution"]


class FileFilters(ListFilters):
    """The filters used for the file_list endpoint."""

    sorting: SortingChoices = None
    albums: List[uuid.UUID] = Field(None, alias="albums")
