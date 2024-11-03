"""API definition and error handlers."""

import logging

from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from ninja import NinjaAPI
from ninja.errors import AuthenticationError
from ninja.errors import HttpError
from ninja.errors import ValidationError

from albums.api import router as albums_router
from files.api import router as files_router
from jobs.api import router as jobs_router
from utils.auth import BMAuthBearer
from utils.parser import ORJSONParser
from utils.parser import ORJSONRenderer
from utils.schema import get_request_metadata_schema

logger = logging.getLogger("bma")

# define the v1 api for JSON
api_v1_json = NinjaAPI(
    version="1",
    parser=ORJSONParser(),
    renderer=ORJSONRenderer(),
    urls_namespace="api-v1-json",
    # the default is for all endpoints to require Bearer auth,
    # but some endpoints override this to also permit anonymous use
    auth=BMAuthBearer(),
)

api_v1_json.add_router("/files/", files_router, tags=["files"])
api_v1_json.add_router("/albums/", albums_router, tags=["albums"])
api_v1_json.add_router("/jobs/", jobs_router, tags=["jobs"])


@api_v1_json.exception_handler(ValidationError)
def custom_validation_errors(request: HttpRequest, exc: ValidationError) -> HttpResponse:
    """Error handler for validation errors."""
    logger.warning(f"ninja validation error: {exc.errors}")
    return api_v1_json.create_response(
        request,
        {
            "bma_request": get_request_metadata_schema(request).dict(),
            "message": "A validation error was encountered. The django-ninja error message is included in details.",
            "details": exc.errors,
        },
        status=422,
    )


@api_v1_json.exception_handler(AuthenticationError)
def custom_authentication_errors(request: HttpRequest, exc: AuthenticationError) -> HttpResponse:
    """Error handler for authentication errors."""
    logger.warning(f"ninja authentication error: {exc}")
    return api_v1_json.create_response(
        request,
        {
            "bma_request": get_request_metadata_schema(request).dict(),
            "message": "An authentication error was encountered. More information in details.",
            "details": str(exc),
        },
        status=403,
    )


@api_v1_json.exception_handler(HttpError)
def custom_http_errors(request: HttpRequest, exc: HttpError) -> HttpResponse:
    """Error handler for HTTP error codes."""
    logger.warning(f"ninja HTTP error: {exc}")
    return api_v1_json.create_response(
        request,
        {
            "bma_request": get_request_metadata_schema(request).dict(),
            "message": "An HTTP error was raised. More information in details.",
            "details": str(exc),
        },
        status=exc.status_code,
    )


@api_v1_json.exception_handler(Http404)
def custom_404_errors(request: HttpRequest, exc: Http404) -> HttpResponse:
    """Error handler for 404 errors."""
    logger.warning(f"ninja 404 error: {exc.args}")
    return api_v1_json.create_response(
        request,
        {
            "bma_request": get_request_metadata_schema(request).dict(),
            "message": "Resource not found. More information in details.",
            "details": str(exc),
        },
        status=404,
    )
