import os
from utils.schema import RequestMetadataSchema
from django.utils import timezone
from guardian.shortcuts import get_perms, get_user_perms, get_group_perms
import uuid
from pathlib import Path
from typing import List
from typing import Optional

from django.urls import reverse
from ninja import ModelSchema
from ninja import Schema

from .models import FileTypeChoices
from .models import LicenseChoices
from .models import StatusChoices
from files.models import BaseFile, StatusChoices
from utils.filters import SortingChoices
from utils.schema import ApiMessageSchema, ApiResponseSchema, ObjectPermissionSchema
from utils.permissions import get_object_permissions_schema
from utils.request import context_request


class UploadRequestSchema(ModelSchema):
    """File metatata."""

    license: LicenseChoices
    title: str = ""
    description: str = ""
    source: str = ""
    thumbnail_url: str = ""

    class Config:
        model = BaseFile
        model_fields = [
            "license",
            "attribution",
            "title",
            "description",
            "source",
            "thumbnail_url",
        ]


class FileUpdateRequestSchema(ModelSchema):
    title: Optional[str] = ""
    description: Optional[str] = ""
    source: Optional[str] = ""
    license: Optional[str] = ""
    attribution: Optional[str] = ""
    thumbnail_url: Optional[str] = ""

    class Config:
        model = BaseFile
        model_fields = [
            "title",
            "description",
            "source",
            "license",
            "attribution",
            "thumbnail_url",
        ]


class MultipleFileRequestSchema(Schema):
    """The schema used for requests involving multiple files."""
    files: List[uuid.UUID]


"""Response schemas below here."""


class FileResponseSchema(ModelSchema):
    albums: List[uuid.UUID] = []
    filename: str
    links: dict
    filetype: str
    filetype_icon: str
    status: str
    status_icon: str
    size_bytes: int
    permissions: ObjectPermissionSchema

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
            "thumbnail_url",
        ]

    @staticmethod
    def resolve_albums(obj, request):
        return [str(x) for x in obj.albums.values_list("uuid", flat=True)]

    @staticmethod
    def resolve_filename(obj, request):
        return Path(obj.original.path).name

    @staticmethod
    def resolve_size_bytes(obj, request):
        if os.path.exists(obj.original.path):
            return obj.original.size
        else:
            return 0

    @staticmethod
    def resolve_links(obj, request):
        links = {
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
            "downloads": {
                "original": obj.original.url,
            },
        }
        if obj.filetype == "picture":
            try:
                links["downloads"].update(
                    {
                        "small_thumbnail": obj.small_thumbnail.url,
                        "medium_thumbnail": obj.medium_thumbnail.url,
                        "large_thumbnail": obj.large_thumbnail.url,
                        "small": obj.small.url,
                        "medium": obj.medium.url,
                        "large": obj.large.url,
                        "slideshow": obj.slideshow.url,
                    },
                )
            except OSError:
                # maybe file is missing from disk
                pass
        return links

    @staticmethod
    def resolve_status(obj, request):
        return StatusChoices[obj.status].label

    @staticmethod
    def resolve_permissions(obj, request):
        return get_object_permissions_schema(obj, request)


class SingleFileResponseSchema(ApiResponseSchema):
    """The schema used to return a response with a single file object."""
    bma_response: FileResponseSchema


class MultipleFileResponseSchema(ApiResponseSchema):
    """The schema used to return a response with multiple file objects."""
    bma_response: List[FileResponseSchema]
