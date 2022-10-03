import logging

from django.http import Http404
from ninja import NinjaAPI
from ninja.errors import AuthenticationError
from ninja.errors import ValidationError
from ninja.security import django_auth

from albums.api import router as albums_router
from files.api import router as files_router
from utils.parser import ORJSONParser
from utils.parser import ORJSONRenderer

logger = logging.getLogger("bma")

# define the v1 api for various formats
api_v1_json = NinjaAPI(
    version="1",
    # we require CSRF but disable it for non-session auth requests
    # inside ExemptOauthFromCSRFMiddleware
    csrf=True,
    parser=ORJSONParser(),
    renderer=ORJSONRenderer(),
    urls_namespace="api-v1-json",
    auth=django_auth,
)

api_v1_json.add_router("/files/", files_router, tags=["files"])
api_v1_json.add_router("/albums/", albums_router, tags=["albums"])


@api_v1_json.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    logger.warning(f"ninja validation error: {exc.errors}")
    return api_v1_json.create_response(request, {"message": exc.errors}, status=422)


@api_v1_json.exception_handler(AuthenticationError)
def custom_authentication_errors(request, exc):
    logger.warning("ninja authentication error")
    return api_v1_json.create_response(
        request,
        {"message": "authentication error"},
        status=403,
    )


@api_v1_json.exception_handler(Http404)
def custom_404_errors(request, exc):
    logger.warning(f"ninja 404 error: {exc.args}")
    return api_v1_json.create_response(
        request,
        {"message": "Resource not found"},
        status=404,
    )
