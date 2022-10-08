import uuid
from pathlib import Path
from typing import List
from typing import Optional

from django.urls import reverse
from ninja import Field
from ninja import ModelSchema
from ninja import Schema

from .models import StatusChoices
from files.models import BaseFile
from utils.license import LicenseChoices
from utils.schema import ListFilters
from utils.schema import SortingChoices


class UploadMetadata(ModelSchema):
    """File metatata."""

    license: LicenseChoices
    title: str = ""
    description: str = ""
    source: str = ""

    class Config:
        model = BaseFile
        model_fields = ["license", "attribution", "title", "description", "source"]


class LinkSchema(Schema):
    self: str
    approve: str
    unpublish: str
    publish: str


class FileOutSchema(ModelSchema):
    albums: List[str] = []
    filename: str
    url: str
    links: LinkSchema

    class Config:
        model = BaseFile
        model_fields = [
            "uuid",
            "owner",
            "created",
            "updated",
            "title",
            "description",
            "source",
            "license",
            "attribution",
            "status",
            "original_filename",
        ]

    def resolve_albums(self, obj):
        return [str(x) for x in obj.albums.values_list("uuid", flat=True)]

    def resolve_filename(self, obj):
        return Path(obj.original.path).name

    def resolve_url(self, obj):
        return obj.original.url

    def resolve_links(self, obj):
        return {
            "self": reverse("api-v1-json:file_get", kwargs={"file_uuid": obj.uuid}),
            "approve": reverse(
                "api-v1-json:file_approve",
                kwargs={"file_uuid": obj.uuid},
            ),
            "unpublish": reverse(
                "api-v1-json:file_unpublish",
                kwargs={"file_uuid": obj.uuid},
            ),
            "publish": reverse(
                "api-v1-json:file_publish",
                kwargs={"file_uuid": obj.uuid},
            ),
        }


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
    statuses: List[StatusChoices] = None
