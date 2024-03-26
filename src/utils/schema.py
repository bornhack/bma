from django.db import models
from ninja import Schema, ModelSchema
from typing import Union, Optional, Any, List
import datetime
from django.utils import timezone
from .request import context_request

class RequestMetadataSchema(Schema):
    """The schema used for the request object in the root of all responses."""
    request_time: datetime.datetime
    username: Optional[str]
    client_ip: Optional[str]


class ApiMessageSchema(Schema):
    """The schema used for all API responses which are just messages."""

    bma_request: RequestMetadataSchema
    message: str = None
    details: dict = None

    @staticmethod
    def resolve_bma_request(obj, context):
        request = context["request"]
        username = request.user.username
        ip = request.META["REMOTE_ADDR"]
        return RequestMetadataSchema(
            request_time=timezone.now(),
            username=username,
            # TODO proxy x-forwarded-for etc support
            client_ip=ip,
        )


class ApiResponseSchema(ApiMessageSchema, Schema):
    """The schema used for all API responses."""
    bma_response: Optional[Any]


class ObjectPermissionSchema(Schema):
    """The schema used to include current users permissions for objects."""
    user_permissions: List[str]
    group_permissions: List[str]
    effective_permissions: List[str]
