"""API schemas used across multiple apps."""

import datetime
import logging
from typing import Any

from django.http import HttpRequest
from django.utils import timezone
from ninja import Schema

logger = logging.getLogger("bma")


class RequestMetadataSchema(Schema):
    """The schema used for the request object in the root of all responses."""

    request_time: datetime.datetime
    username: str
    client_ip: str

    @staticmethod
    def resolve_request_time(obj: dict[str, str]) -> datetime.datetime:
        """Get the value for the request_time field."""
        return timezone.now()

    @staticmethod
    def resolve_username(obj: dict[str, str], context: dict[str, HttpRequest]) -> str:
        """Get the value for the username field."""
        request = context["request"]
        return str(request.user.username)

    @staticmethod
    def resolve_client_ip(obj: dict[str, str], context: dict[str, HttpRequest]) -> str:
        """Get the value for the client_ip field."""
        request = context["request"]
        return str(request.META["REMOTE_ADDR"])


def get_request_metadata_schema(request: HttpRequest) -> RequestMetadataSchema:
    """Init and populate an instance of the schema."""
    return RequestMetadataSchema.construct(
        request_time=timezone.now(), username=request.user.username, client_ip=request.META["REMOTE_ADDR"]
    )


class ApiMessageSchema(Schema):
    """The schema used for all API responses which are just messages."""

    bma_request: RequestMetadataSchema
    message: str = "OK"
    details: dict[str, str] | None = None

    @staticmethod
    def resolve_bma_request(obj: dict[str, str], context: dict[str, HttpRequest]) -> RequestMetadataSchema:
        """Populate and return a RequestMetadataSchema object for the bma_request field."""
        return RequestMetadataSchema.construct()


class ApiResponseSchema(ApiMessageSchema):
    """The schema used for all API responses which contain a bma_response object."""

    bma_response: Any


class ObjectPermissionSchema(Schema):
    """The schema used to include current permissions for objects."""

    user_permissions: list[str]
    group_permissions: list[str]
    effective_permissions: list[str]
